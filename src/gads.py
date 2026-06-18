"""
Google Ads konektor - stažení dat z Google Ads API do pandas DataFrame.

Napojení na účet (např. "panopro") probíhá přes oficiální knihovnu
``google-ads``. Konfigurace se načítá v tomto pořadí:

1. slovník předaný přímo do konstruktoru (``config_dict``)
2. YAML soubor (default ``google-ads.yaml`` v kořeni projektu)
3. proměnné prostředí (``GOOGLE_ADS_*``)

Citlivé údaje (developer token, OAuth refresh token...) NIKDY nepatří do
gitu - ukládej je do ``google-ads.yaml`` nebo ``.env`` (oba jsou v .gitignore).
"""

import enum
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# python-dotenv je v requirements; načteme .env, pokud existuje
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv je volitelný
    pass


# Výchozí cesta ke konfiguračnímu YAML souboru
DEFAULT_CONFIG_PATH = Path("google-ads.yaml")

# Standardní report výkonu kampaní
CAMPAIGN_PERFORMANCE_FIELDS = [
    "campaign.id",
    "campaign.name",
    "campaign.status",
    "metrics.impressions",
    "metrics.clicks",
    "metrics.ctr",
    "metrics.average_cpc",
    "metrics.cost_micros",
    "metrics.conversions",
    "metrics.conversions_value",
]


def _to_python(value: Any) -> Any:
    """Převede hodnotu z proto-plus na čistý Python typ (enum -> název)."""
    if isinstance(value, enum.Enum):
        return value.name
    return value


def _traverse(row: Any, field_path: str) -> Any:
    """Projde tečkovou cestu (např. 'campaign.name') na řádku výsledku."""
    obj = row
    for part in field_path.split("."):
        obj = getattr(obj, part)
    return _to_python(obj)


def _parse_select_fields(query: str) -> List[str]:
    """Vytáhne názvy sloupců z části SELECT ... FROM dotazu GAQL."""
    match = re.search(r"SELECT\s+(.*?)\s+FROM", query, re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError("Neplatný GAQL dotaz: chybí SELECT ... FROM.")
    fields = [f.strip() for f in match.group(1).split(",")]
    return [f for f in fields if f]


def _clean_customer_id(customer_id: Optional[str]) -> Optional[str]:
    """Odstraní pomlčky a mezery z ID účtu (Google Ads chce jen číslice)."""
    if customer_id is None:
        return None
    return re.sub(r"[^0-9]", "", str(customer_id))


class GoogleAdsConnector:
    """Konektor pro stahování dat z Google Ads API."""

    def __init__(
        self,
        customer_id: Optional[str] = None,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            customer_id: ID Google Ads účtu (panopro), např. "123-456-7890".
                Když není zadáno, vezme se z env ``GOOGLE_ADS_CUSTOMER_ID``.
            config_path: Cesta ke google-ads.yaml (default ./google-ads.yaml).
            config_dict: Konfigurace přímo jako slovník (má přednost).
        """
        import os

        self.customer_id = _clean_customer_id(
            customer_id or os.getenv("GOOGLE_ADS_CUSTOMER_ID")
        )
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.config_dict = config_dict
        self._client = None

    @staticmethod
    def _import_client():
        """Líný import knihovny google-ads s přívětivou chybou."""
        try:
            from google.ads.googleads.client import GoogleAdsClient

            return GoogleAdsClient
        except ImportError as exc:
            raise ImportError(
                "Knihovna 'google-ads' není nainstalovaná. "
                "Spusť: pip install google-ads"
            ) from exc

    @property
    def client(self):
        """Vytvoří (a nacachuje) Google Ads klienta podle konfigurace."""
        if self._client is not None:
            return self._client

        GoogleAdsClient = self._import_client()

        if self.config_dict:
            self._client = GoogleAdsClient.load_from_dict(self.config_dict)
        elif self.config_path.exists():
            self._client = GoogleAdsClient.load_from_storage(str(self.config_path))
        else:
            # poslední možnost: proměnné prostředí GOOGLE_ADS_*
            self._client = GoogleAdsClient.load_from_env()

        return self._client

    def search(
        self,
        query: str,
        customer_id: Optional[str] = None,
        convert_micros: bool = True,
    ) -> pd.DataFrame:
        """
        Spustí libovolný GAQL dotaz a vrátí výsledek jako DataFrame.

        Args:
            query: Dotaz v Google Ads Query Language.
            customer_id: ID účtu (jinak self.customer_id).
            convert_micros: Sloupce *_micros vydělí 1e6 a přejmenuje
                (cost_micros -> cost) na reálnou měnu.
        """
        cid = _clean_customer_id(customer_id) or self.customer_id
        if not cid:
            raise ValueError(
                "Chybí customer_id. Zadej ho do konstruktoru, do metody, "
                "nebo do env GOOGLE_ADS_CUSTOMER_ID."
            )

        fields = _parse_select_fields(query)
        service = self.client.get_service("GoogleAdsService")

        rows: List[Dict[str, Any]] = []
        try:
            stream = service.search_stream(customer_id=cid, query=query)
            for batch in stream:
                for row in batch.results:
                    rows.append({f: _traverse(row, f) for f in fields})
        except Exception as exc:  # GoogleAdsException i ostatní
            raise RuntimeError(self._format_error(exc)) from exc

        df = pd.DataFrame(rows, columns=fields)
        if convert_micros:
            df = self._convert_micros(df)
        return df

    def fetch_campaign_performance(
        self,
        days: int = 30,
        customer_id: Optional[str] = None,
        by_date: bool = False,
    ) -> pd.DataFrame:
        """
        Stáhne výkon kampaní (imprese, kliky, cena, konverze) za posledních N dní.

        Args:
            days: Počet dní zpět (default 30).
            customer_id: ID účtu (jinak self.customer_id).
            by_date: True = řádky rozpadnuté po dnech, False = souhrn za období.
        """
        end = date.today()
        start = end - timedelta(days=days)

        fields = list(CAMPAIGN_PERFORMANCE_FIELDS)
        if by_date:
            fields.insert(0, "segments.date")

        query = (
            f"SELECT {', '.join(fields)} "
            "FROM campaign "
            f"WHERE segments.date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}' "
            "ORDER BY metrics.cost_micros DESC"
        )
        return self.search(query, customer_id=customer_id)

    @staticmethod
    def _convert_micros(df: pd.DataFrame) -> pd.DataFrame:
        """Převede sloupce končící na _micros na reálnou měnu."""
        rename = {}
        for col in df.columns:
            if col.endswith("_micros"):
                df[col] = pd.to_numeric(df[col], errors="coerce") / 1_000_000
                rename[col] = col[: -len("_micros")]
        return df.rename(columns=rename)

    @staticmethod
    def _format_error(exc: Exception) -> str:
        """Sestaví čitelné hlášku z chyby Google Ads API."""
        request_id = getattr(exc, "request_id", None)
        failure = getattr(exc, "failure", None)
        if failure is not None:
            details = "; ".join(
                getattr(err, "message", str(err)) for err in failure.errors
            )
            return f"Google Ads API chyba (request_id={request_id}): {details}"
        return f"Chyba při dotazu do Google Ads API: {exc}"

    def to_analyzer(self, df: pd.DataFrame, name: str = "google_ads"):
        """Zabalí DataFrame do DataAnalyzeru pro další analýzu."""
        from .analyzer import DataAnalyzer

        return DataAnalyzer.from_dataframe(df, name=name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Stáhne výkon kampaní z Google Ads účtu (panopro)."
    )
    parser.add_argument(
        "--customer-id", help="ID Google Ads účtu (jinak z env GOOGLE_ADS_CUSTOMER_ID)"
    )
    parser.add_argument("--days", type=int, default=30, help="Počet dní zpět")
    parser.add_argument("--config", help="Cesta ke google-ads.yaml")
    parser.add_argument("--csv", help="Kam uložit výsledek jako CSV")
    parser.add_argument(
        "--by-date", action="store_true", help="Rozpad po dnech místo souhrnu"
    )
    args = parser.parse_args()

    connector = GoogleAdsConnector(
        customer_id=args.customer_id, config_path=args.config
    )
    data = connector.fetch_campaign_performance(days=args.days, by_date=args.by_date)
    print(f"✓ Staženo {len(data)} řádků z Google Ads")

    if args.csv:
        data.to_csv(args.csv, index=False, encoding="utf-8")
        print(f"✓ Uloženo do {args.csv}")

    # rovnou souhrnná analýza
    connector.to_analyzer(data).print_report()
