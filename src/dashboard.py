"""
Interaktivní dashboard (Streamlit) pro Data Analyst Claude.

Spuštění z kořene projektu:
    streamlit run src/dashboard.py

Funkce:
- nahrání CSV nebo výběr ze složky data/
- přehled dat, numerické statistiky a grafy
- marketingová KPI (CTR, CPC, konverzní poměr, cena/konverze) + tabulka kampaní
- vývoj v čase (když data obsahují datum)
- export statistik (CSV) i AI insightů (.md)
- AI insighty od Clauda na jedno tlačítko (vyžaduje ANTHROPIC_API_KEY)
- responzivní zobrazení, připraveno na nasazení (Streamlit Community Cloud)

Nasazení na web: viz DEPLOY.md.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Umožní spuštění přes `streamlit run src/dashboard.py`
# (přidá kořen projektu na importní cestu, ať jde importovat balíček src)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analyzer import DataAnalyzer  # noqa: E402
from src.ai import ClaudeAnalyst  # noqa: E402

DATA_DIR = ROOT / "data"

# Na Streamlit Cloud se tajné hodnoty zadávají v Secrets. Přemostíme klíč do
# prostředí, aby ho ClaudeAnalyst (čte ANTHROPIC_API_KEY z env) našel i v cloudu.
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ.setdefault("ANTHROPIC_API_KEY", str(st.secrets["ANTHROPIC_API_KEY"]))
except Exception:  # lokálně bez secrets.toml je to v pořádku
    pass

# Aliasy pro automatické rozpoznání marketingových sloupců (CZ i EN, i metrics.*)
COL_GUESS = {
    "Náklady": ["cost", "náklady", "naklady", "spend", "útrata", "utrata", "metrics.cost"],
    "Prokliky": ["clicks", "prokliky", "kliknutí", "kliknuti", "metrics.clicks"],
    "Imprese": ["impr", "imprese", "impressions", "zobrazení", "zobrazeni", "metrics.impressions"],
    "Konverze": ["conversions", "konverze", "poptávky", "poptavky", "metrics.conversions"],
    "Kampaň": ["campaign", "kampaň", "kampan", "campaign.name"],
    "Datum": ["date", "datum", "day", "den", "segments.date"],
}


def check_password() -> bool:
    """
    Volitelná ochrana heslem pro veřejné nasazení.

    Když je v Secrets nastaveno ``APP_PASSWORD``, vyžádá si heslo (jinak je
    aplikace otevřená — vhodné pro lokální běh). Chrání API klíč i data při
    veřejném nasazení.
    """
    try:
        pw = st.secrets["APP_PASSWORD"] if "APP_PASSWORD" in st.secrets else None
    except Exception:
        pw = None
    if not pw:
        return True
    if st.session_state.get("auth_ok"):
        return True
    entered = st.text_input("Heslo pro přístup", type="password")
    if entered and entered == str(pw):
        st.session_state["auth_ok"] = True
        return True
    if entered:
        st.error("Špatné heslo.")
    st.stop()


def load_csv(path_or_buffer) -> pd.DataFrame:
    """Načte CSV z cesty nebo z nahraného souboru."""
    return pd.read_csv(path_or_buffer)


def list_data_csvs() -> list:
    """Vrátí názvy CSV souborů ve složce data/."""
    if DATA_DIR.exists():
        return sorted(p.name for p in DATA_DIR.glob("*.csv"))
    return []


def guess_col(df: pd.DataFrame, key: str):
    """Tipne sloupec podle aliasů (přesná shoda > začíná na > obsahuje)."""
    lower = {c.lower().strip(): c for c in df.columns}
    aliases = COL_GUESS[key]
    for a in aliases:
        if a in lower:
            return lower[a]
    for c in df.columns:
        cl = c.lower().strip()
        if any(cl.startswith(a) or a in cl for a in aliases):
            return c
    return None


def fmt(n, suffix: str = "") -> str:
    """Číslo bez desetin s mezerou jako oddělovačem tisíců (1 234)."""
    try:
        return f"{n:,.0f}{suffix}".replace(",", " ")
    except (ValueError, TypeError):
        return "—"


def fmt2(n, suffix: str = "") -> str:
    """Číslo na 2 desetinná místa s mezerou u tisíců."""
    try:
        return f"{n:,.2f}{suffix}".replace(",", " ")
    except (ValueError, TypeError):
        return "—"


def col_sum(df: pd.DataFrame, col):
    """Součet číselného sloupce (nečíselné hodnoty ignoruje); None když sloupec není."""
    if not col:
        return None
    return pd.to_numeric(df[col], errors="coerce").sum()


def main():
    st.set_page_config(
        page_title="Data Analyst Claude",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="auto",
    )
    # Lehký vizuální styl (čistší vzhled, hezčí KPI karty). Když se Streamlit
    # interně změní, styl se prostě neaplikuje — nic se nerozbije.
    st.markdown(
        """
        <style>
          #MainMenu, footer {visibility: hidden;}
          .block-container {padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1300px;}
          div[data-testid="stMetric"] {
            background: #f7f9fc; border: 1px solid #e6e9ef;
            border-radius: 12px; padding: 12px 16px;
          }
          div[data-testid="stMetricLabel"] p {opacity: .7; font-size: .85rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("📊 Data Analyst Claude")
    st.caption("Analýza dat · marketingová KPI · AI insighty od Clauda")

    check_password()

    # --- Postranní panel: zdroj dat ---
    st.sidebar.header("Zdroj dat")
    uploaded = st.sidebar.file_uploader("Nahraj CSV", type=["csv"])

    chosen = None
    existing = list_data_csvs()
    if existing:
        pick = st.sidebar.selectbox("…nebo vyber ze složky data/", ["—"] + existing)
        chosen = None if pick == "—" else pick

    df = None
    source_name = "data"
    if uploaded is not None:
        df = load_csv(uploaded)
        source_name = uploaded.name
    elif chosen:
        df = load_csv(DATA_DIR / chosen)
        source_name = chosen

    if df is None:
        st.info("⬅️ Nahraj CSV, nebo vyber soubor ze složky `data/` v levém panelu.")
        st.stop()

    analyzer = DataAnalyzer.from_dataframe(df, name=source_name)
    summary = analyzer.generate_summary()

    # --- Přehled ---
    st.subheader(f"Přehled — {source_name}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Řádky", fmt(summary["rows"]))
    c2.metric("Sloupce", summary["columns"])
    c3.metric("Chybějící hodnoty", fmt(sum(summary["missing_values"].values())))
    with st.expander("Náhled dat"):
        st.dataframe(df.head(50), use_container_width=True)

    # --- Mapování marketingových sloupců (auto-tip + možnost změnit) ---
    st.sidebar.header("Marketingová KPI")
    st.sidebar.caption("Přiřazení sloupců — automaticky natipnuto, lze přepnout.")
    options = ["—"] + list(df.columns)

    def picker(label):
        guess = guess_col(df, label)
        idx = options.index(guess) if guess in options else 0
        sel = st.sidebar.selectbox(label, options, index=idx, key=f"map_{label}")
        return None if sel == "—" else sel

    col_cost = picker("Náklady")
    col_clicks = picker("Prokliky")
    col_impr = picker("Imprese")
    col_conv = picker("Konverze")
    col_campaign = picker("Kampaň")
    col_date = picker("Datum")

    total_cost = col_sum(df, col_cost)
    total_clicks = col_sum(df, col_clicks)
    total_impr = col_sum(df, col_impr)
    total_conv = col_sum(df, col_conv)

    # --- Marketingová KPI ---
    if any(v is not None for v in (total_cost, total_clicks, total_impr, total_conv)):
        st.divider()
        st.subheader("Marketingová KPI")
        row1 = st.columns(4)
        if total_cost is not None:
            row1[0].metric("Náklady", fmt(total_cost, " Kč"))
        if total_clicks is not None:
            row1[1].metric("Prokliky", fmt(total_clicks))
        if total_impr is not None:
            row1[2].metric("Imprese", fmt(total_impr))
        if total_conv is not None:
            row1[3].metric("Konverze", fmt2(total_conv))

        row2 = st.columns(4)
        if total_clicks and total_impr:
            row2[0].metric("CTR", fmt2(100 * total_clicks / total_impr, " %"))
        if total_cost is not None and total_clicks:
            row2[1].metric("Prům. CPC", fmt2(total_cost / total_clicks, " Kč"))
        if total_conv and total_clicks:
            row2[2].metric("Konverzní poměr", fmt2(100 * total_conv / total_clicks, " %"))
        if total_cost is not None and total_conv:
            row2[3].metric("Cena/konverze", fmt2(total_cost / total_conv, " Kč"))

    # --- Výkon podle kampaní ---
    if col_campaign:
        agg = {c: "sum" for c in (col_cost, col_clicks, col_impr, col_conv) if c}
        if agg:
            st.divider()
            st.subheader("Výkon podle kampaní")
            t = df.copy()
            for c in agg:
                t[c] = pd.to_numeric(t[c], errors="coerce")
            tbl = t.groupby(col_campaign, dropna=False).agg(agg)
            if col_cost and col_conv:
                tbl["Cena/konverze"] = (tbl[col_cost] / tbl[col_conv]).round(2)
            if col_clicks and col_impr:
                tbl["CTR %"] = (100 * tbl[col_clicks] / tbl[col_impr]).round(2)
            tbl = tbl.sort_values(col_cost or next(iter(agg)), ascending=False)
            # Hezčí formát čísel (měna/procenta). Když starší Streamlit verze
            # column_config nezná, spadne to do prostého zobrazení tabulky.
            try:
                cc = {}
                if col_cost:
                    cc[col_cost] = st.column_config.NumberColumn("Náklady", format="%.0f Kč")
                if col_clicks:
                    cc[col_clicks] = st.column_config.NumberColumn("Prokliky", format="%d")
                if col_impr:
                    cc[col_impr] = st.column_config.NumberColumn("Imprese", format="%d")
                if col_conv:
                    cc[col_conv] = st.column_config.NumberColumn("Konverze", format="%.2f")
                if "Cena/konverze" in tbl.columns:
                    cc["Cena/konverze"] = st.column_config.NumberColumn(format="%.2f Kč")
                if "CTR %" in tbl.columns:
                    cc["CTR %"] = st.column_config.NumberColumn(format="%.2f %%")
                st.dataframe(tbl, use_container_width=True, column_config=cc or None)
            except Exception:
                st.dataframe(tbl, use_container_width=True)

    # --- Vývoj v čase ---
    if col_date and (col_cost or col_conv or col_clicks):
        st.divider()
        st.subheader("Vývoj v čase")
        t = df.copy()
        t[col_date] = pd.to_datetime(t[col_date], errors="coerce")
        metrics = [c for c in (col_cost, col_conv, col_clicks) if c]
        for c in metrics:
            t[c] = pd.to_numeric(t[c], errors="coerce")
        ts = t.dropna(subset=[col_date]).groupby(col_date)[metrics].sum()
        if not ts.empty:
            st.line_chart(ts, use_container_width=True)

    # --- Numerické statistiky (+ export) ---
    stats = analyzer.get_numeric_statistics()
    if stats:
        st.divider()
        st.subheader("Numerické statistiky")
        stats_df = pd.DataFrame(stats).T
        st.dataframe(stats_df, use_container_width=True)
        st.download_button(
            "⬇️ Stáhnout statistiky (CSV)",
            stats_df.to_csv().encode("utf-8"),
            file_name=f"statistiky_{source_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # --- Obecný graf ---
    numeric_cols = df.select_dtypes("number").columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols]
    if numeric_cols:
        st.divider()
        st.subheader("Graf")
        col_m, col_d = st.columns(2)
        metric = col_m.selectbox("Metrika", numeric_cols)
        dim = col_d.selectbox("Rozměr (popisek)", ["(index)"] + cat_cols)
        if dim != "(index)":
            data = df.groupby(dim)[metric].sum().sort_values(ascending=False).head(20)
        else:
            data = df[metric]
        st.bar_chart(data, use_container_width=True)

    # --- Outliers ---
    outliers = analyzer.detect_outliers()
    if outliers:
        with st.expander(f"⚠️ Detekované outliers ({len(outliers)} sloupců)"):
            for col, idx in outliers.items():
                st.write(f"**{col}**: {len(idx)} outlierů (řádky {idx[:10]}…)")

    # --- AI insighty (+ export) ---
    st.divider()
    st.subheader("🤖 AI insighty (Claude)")
    extra = st.text_input(
        "Doplňující kontext (volitelně)",
        placeholder="např. účet panopro, pasport stavby",
    )
    if st.button("Vygenerovat AI insighty", type="primary"):
        with st.spinner("Claude přemýšlí…"):
            try:
                st.session_state["insights"] = ClaudeAnalyst().insights(
                    summary, extra=extra or None
                )
            except Exception as exc:  # chybějící klíč i chyby API
                st.session_state["insights"] = None
                st.error(str(exc))
                st.caption("Tip: klíč nastav v .env (lokálně) nebo v Secrets (cloud).")

    if st.session_state.get("insights"):
        st.markdown(st.session_state["insights"])
        st.download_button(
            "⬇️ Stáhnout insighty (.md)",
            st.session_state["insights"].encode("utf-8"),
            file_name=f"insighty_{source_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
