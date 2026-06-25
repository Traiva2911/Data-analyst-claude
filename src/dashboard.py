"""
Interaktivní dashboard (Streamlit) pro Data Analyst Claude.

Spuštění z kořene projektu:
    streamlit run src/dashboard.py

Funkce:
- nahrání CSV nebo výběr ze složky data/
- přehled dat, numerické statistiky a grafy
- AI insighty od Clauda na jedno tlačítko (vyžaduje ANTHROPIC_API_KEY v .env)
"""

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


def load_csv(path_or_buffer) -> pd.DataFrame:
    """Načte CSV z cesty nebo z nahraného souboru."""
    return pd.read_csv(path_or_buffer)


def list_data_csvs() -> list:
    """Vrátí názvy CSV souborů ve složce data/."""
    if DATA_DIR.exists():
        return sorted(p.name for p in DATA_DIR.glob("*.csv"))
    return []


def chart_data(df: pd.DataFrame, metric: str, dim: str):
    """Připraví data pro sloupcový graf (metrika podle rozměru, nebo dle indexu)."""
    if dim and dim != "(index)":
        return df.groupby(dim)[metric].sum().sort_values(ascending=False).head(20)
    return df[metric]


def main():
    st.set_page_config(
        page_title="Data Analyst Claude", page_icon="📊", layout="wide"
    )
    st.title("📊 Data Analyst Claude")
    st.caption("Analýza dat + AI insighty od Clauda")

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
    c1.metric("Řádky", summary["rows"])
    c2.metric("Sloupce", summary["columns"])
    c3.metric("Chybějící hodnoty", int(sum(summary["missing_values"].values())))

    with st.expander("Náhled dat"):
        st.dataframe(df.head(50))

    # --- Numerické statistiky ---
    stats = analyzer.get_numeric_statistics()
    if stats:
        st.subheader("Numerické statistiky")
        st.dataframe(pd.DataFrame(stats).T)

    # --- Graf ---
    numeric_cols = df.select_dtypes("number").columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols]
    if numeric_cols:
        st.subheader("Graf")
        col_m, col_d = st.columns(2)
        metric = col_m.selectbox("Metrika", numeric_cols)
        dim = col_d.selectbox("Rozměr (popisek)", ["(index)"] + cat_cols)
        st.bar_chart(chart_data(df, metric, dim))

    # --- Outliers ---
    outliers = analyzer.detect_outliers()
    if outliers:
        with st.expander(f"⚠️ Detekované outliers ({len(outliers)} sloupců)"):
            for col, idx in outliers.items():
                st.write(f"**{col}**: {len(idx)} outlierů (řádky {idx[:10]}…)")

    # --- AI insighty ---
    st.subheader("🤖 AI insighty (Claude)")
    extra = st.text_input(
        "Doplňující kontext (volitelně)",
        placeholder="např. účet panopro, pasport stavby",
    )
    if st.button("Vygenerovat AI insighty", type="primary"):
        with st.spinner("Claude přemýšlí…"):
            try:
                text = ClaudeAnalyst().insights(summary, extra=extra or None)
                st.markdown(text)
            except Exception as exc:  # chybějící klíč i chyby API
                st.error(str(exc))
                st.caption("Tip: klíč nastav v souboru .env jako ANTHROPIC_API_KEY.")


if __name__ == "__main__":
    main()
