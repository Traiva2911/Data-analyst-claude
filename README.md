# Data Analyst Claude

Inteligentní nástroj pro analýzu dat s podporou Claude AI. Automaticky načítá CSV soubory, generuje statistické analýzy a vytváří insights.

## ✨ Vlastnosti

- 📊 Automatická analýza CSV souborů
- 📈 Deskriptivní statistika a trendy
- 🔍 Detekce anomálií
- 📝 Generování reportů
- 🤖 Integrace s Claude AI
- 💾 Podpora více datových formátů

## 🚀 Instalace

```bash
git clone https://github.com/Traiva2911/Data-analyst-claude.git
cd Data-analyst-claude
pip install -r requirements.txt
```

## 📖 Použití

```python
from src.analyzer import DataAnalyzer

# Načti a analyzuj data
analyzer = DataAnalyzer('data/your_file.csv')
summary = analyzer.generate_summary()
print(summary)
```

### Příklady

```bash
# Analýza jediného souboru
python -m src.analyzer data/sample.csv

# Analýza více souborů
python -m src.analyzer data/*.csv
```

## 📣 Napojení na Google Ads

Projekt umí stáhnout data přímo z Google Ads API (např. z účtu **panopro**)
a rovnou je zanalyzovat.

### 1. Co budeš potřebovat

| Údaj | Kde ho získáš |
|------|---------------|
| **Developer token** | Google Ads → nástroje → API Center (na MCC účtu) |
| **OAuth2 client_id + client_secret** | Google Cloud Console → Credentials → OAuth client (typ *Desktop app*) |
| **Refresh token** | Vygeneruje přiložený skript `python -m src.generate_refresh_token` (viz níže) |
| **login_customer_id** | ID správcovského (MCC) účtu, bez pomlček |
| **customer_id** | ID účtu *panopro*, ze kterého stahuješ data |

### 2. Konfigurace

Zkopíruj šablony a doplň své hodnoty (oba soubory jsou v `.gitignore`,
takže se tokeny nikdy nedostanou do gitu):

```bash
cp google-ads.yaml.example google-ads.yaml   # tokeny pro API
cp .env.example .env                          # GOOGLE_ADS_CUSTOMER_ID
```

#### Vygenerování refresh_token

Do `google-ads.yaml` vyplň `developer_token`, `client_id` a `client_secret`,
pak spusť skript — otevře prohlížeč, přihlásíš se Google účtem s přístupem
k účtu *panopro* a token se rovnou zapíše do `google-ads.yaml`:

```bash
python -m src.generate_refresh_token --update-yaml
```

> 💡 OAuth client musí být v Google Cloud Console typu **Desktop app**.

### 3. Použití

```python
from src import GoogleAdsConnector

# Konfigurace se načte z google-ads.yaml; customer_id z .env nebo přímo:
connector = GoogleAdsConnector(customer_id="123-456-7890")

# Výkon kampaní za posledních 30 dní jako pandas DataFrame
df = connector.fetch_campaign_performance(days=30)

# Další hotové reporty:
df = connector.fetch_keyword_performance(days=30)   # klíčová slova
df = connector.fetch_ad_performance(days=30)        # inzeráty
df = connector.fetch_daily_trends(days=30)          # denní trend (časová řada)

# Rovnou souhrnná analýza (statistiky, outliers, chybějící hodnoty)
connector.to_analyzer(df, name="panopro").print_report()

# Nebo libovolný vlastní GAQL dotaz
df = connector.search("SELECT campaign.name, metrics.clicks FROM campaign")
```

Z příkazové řádky:

```bash
# Nejdřív ověř připojení (minimální živé volání, vypíše dostupné účty)
python -m src.gads --check

# Stáhne kampaně a uloží do CSV + vytiskne report
python -m src.gads --customer-id 123-456-7890 --days 30 --csv data/panopro.csv

# Jiný report: campaigns (default) | keywords | ads | trends
python -m src.gads --report keywords --days 30
```

> ⚠️ Ceny vrací Google Ads v *micros* (1 000 000 = 1 jednotka měny).
> Konektor je automaticky převede (`cost_micros` → `cost`).

## 📁 Struktura projektu

```
├── src/
│   ├── analyzer.py            # Hlavní analyzer pro data
│   ├── gads.py               # Konektor na Google Ads API
│   ├── generate_refresh_token.py  # OAuth2 refresh_token generátor
│   └── utils.py              # Pomocné funkce
├── data/                     # Složka pro vaše CSV data
├── reports/                  # Vygenerované reporty
├── google-ads.yaml.example   # Šablona konfigurace Google Ads
├── .env.example              # Šablona proměnných prostředí
├── requirements.txt          # Python závislosti
└── README.md                 # Tato dokumentace
```

## 🛠️ Technologie

- **Python 3.8+**
- **pandas** — manipulace s daty
- **numpy** — numerické výpočty
- **matplotlib** — vizualizace
- **google-ads** — napojení na Google Ads API

## 📝 Příspěvky

Přispívání je vítáno! Prosím:

1. Forkuj projekt
2. Vytvoř feature branch (`git checkout -b feature/amazing-feature`)
3. Commitni změny (`git commit -m 'Add amazing feature'`)
4. Pushni branch (`git push origin feature/amazing-feature`)
5. Otevři Pull Request

## 📄 Licence

MIT License — viz LICENSE soubor

## 👤 Autor

Andrea Matis (@Traiva2911)

---

**Poznámka:** Tohoto projektu lze používat pro analýzu vlastních CSV data. Stačí umístit soubory do složky `data/`.
