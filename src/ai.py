"""
Claude AI - generování insightů z analyzovaných dat.

Pošle souhrn dat (z DataAnalyzeru nebo Google Ads reportu) Claudovi přes
oficiální Anthropic API a vrátí srozumitelné insighty a doporučení.

Klíč se bere z proměnné prostředí ``ANTHROPIC_API_KEY`` (nebo z argumentu).
Klíč NIKDY nepatří do gitu - drž ho v .env (je v .gitignore).

Použití:
    from src.ai import ClaudeAnalyst
    from src.analyzer import DataAnalyzer

    summary = DataAnalyzer("data/panopro.csv").generate_summary()
    print(ClaudeAnalyst().insights(summary))
"""

import json
import os
from typing import Any, Dict, Optional

# python-dotenv je v requirements; načteme .env, pokud existuje
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv je volitelný
    pass

# Výchozí model - nejschopnější Claude (viz claude-api reference)
DEFAULT_MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = (
    "Jsi datový analytik. Dostaneš souhrn dat (statistiky, sloupce, případně "
    "výkon Google Ads kampaní). Napiš stručné, konkrétní insighty a doporučení "
    "v češtině jako 3-6 odrážek - bez omáčky. Vycházej výhradně z dodaných "
    "čísel; co z dat nejde určit, výslovně označ jako neznámé."
)


class ClaudeAnalyst:
    """Klient pro generování insightů přes Claude (Anthropic API)."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Args:
            api_key: Anthropic API klíč. Když není zadán, vezme se z env
                ``ANTHROPIC_API_KEY``.
            model: ID modelu (default claude-opus-4-8).
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

    @property
    def client(self):
        """Vytvoří (a nacachuje) Anthropic klienta."""
        if self._client is not None:
            return self._client

        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "Knihovna 'anthropic' není nainstalovaná. "
                "Spusť: pip install anthropic"
            ) from exc

        if not self.api_key:
            raise ValueError(
                "Chybí ANTHROPIC_API_KEY. Nastav proměnnou prostředí "
                "(ideálně v .env), nebo předej api_key do konstruktoru."
            )

        self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def ask(
        self,
        prompt: str,
        system: str = SYSTEM_PROMPT,
        max_tokens: int = 4096,
    ) -> str:
        """
        Pošle prompt Claudovi a vrátí textovou odpověď.

        Args:
            prompt: Uživatelský dotaz / data k interpretaci.
            system: Systémový prompt (chování modelu).
            max_tokens: Strop výstupních tokenů.
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # typované výjimky převedeme na čitelné hlášení
            raise RuntimeError(self._format_error(exc)) from exc

        return "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()

    def insights(
        self, summary: Dict[str, Any], extra: Optional[str] = None
    ) -> str:
        """
        Vygeneruje insighty ze souhrnu dat (např. DataAnalyzer.generate_summary()).

        Args:
            summary: Slovník se souhrnem dat.
            extra: Volitelný doplňující kontext (např. "účet panopro, e-shop").
        """
        payload = json.dumps(summary, ensure_ascii=False, indent=2, default=str)
        prompt = f"Souhrn dat (JSON):\n{payload}"
        if extra:
            prompt += f"\n\nDoplňující kontext: {extra}"
        prompt += "\n\nNapiš insighty a doporučení."
        return self.ask(prompt)

    @staticmethod
    def _format_error(exc: Exception) -> str:
        """Převede chybu Anthropic API na čitelné hlášení."""
        try:
            import anthropic
        except ImportError:
            return f"Chyba volání Anthropic API: {exc}"

        if isinstance(exc, anthropic.AuthenticationError):
            return "Neplatný nebo chybějící ANTHROPIC_API_KEY (401)."
        if isinstance(exc, anthropic.RateLimitError):
            return "Překročen rate limit Anthropic API (429). Zkus to za chvíli."
        if isinstance(exc, anthropic.APIStatusError):
            return (
                f"Anthropic API chyba ({exc.status_code}): "
                f"{getattr(exc, 'message', exc)}"
            )
        return f"Chyba volání Anthropic API: {exc}"


if __name__ == "__main__":
    import sys
    from .analyzer import DataAnalyzer

    if len(sys.argv) < 2:
        print("Použití: python -m src.ai <file.csv>")
        raise SystemExit(1)

    summary = DataAnalyzer(sys.argv[1]).generate_summary()
    print("\n=== AI INSIGHTY (Claude) ===\n")
    print(ClaudeAnalyst().insights(summary))
