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

## 📁 Struktura projektu

```
├── src/
│   ├── analyzer.py       # Hlavní analyzer pro data
│   └── utils.py          # Pomocné funkce
├── data/                 # Složka pro vaše CSV data
├── reports/              # Vygenerované reporty
├── requirements.txt      # Python závislosti
└── README.md             # Tato dokumentace
```

## 🛠️ Technologie

- **Python 3.8+**
- **pandas** — manipulace s daty
- **numpy** — numerické výpočty
- **matplotlib** — vizualizace

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
