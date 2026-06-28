# Nasazení dashboardu na web

Dashboard (`src/dashboard.py`, Streamlit) lze **zdarma** nasadit na **Streamlit
Community Cloud** a sdílet odkazem. Běží pak v prohlížeči na počítači, tabletu
i mobilu (responzivní).

## Předpoklady

- Kód na GitHubu (✓ repo `Traiva2911/marketing-dashboard`).
- Účet na <https://streamlit.io/cloud> (přihlášení přes GitHub, zdarma).
- Anthropic API klíč (pro AI insighty).

## Kroky

1. Jdi na <https://share.streamlit.io> a přihlas se přes GitHub (povol přístup
   k repozitáři).
2. Klikni **Create app → Deploy a public app from GitHub**.
3. Vyplň:
   - **Repository:** `Traiva2911/marketing-dashboard`
   - **Branch:** `claude/beautiful-meitner-538oe8` (nebo `main` po sloučení)
   - **Main file path:** `src/dashboard.py`
4. Rozbal **Advanced settings → Secrets** a vlož (formát TOML):
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   APP_PASSWORD = "zvol-si-heslo"
   ```
5. Klikni **Deploy**. Za chvilku dostaneš veřejnou URL (např.
   `https://<název>.streamlit.app`).

## 🔒 Bezpečnost (důležité)

- **Nastav `APP_PASSWORD`.** Bez něj je aplikace veřejná a kdokoli s odkazem může
  klikat na „Vygenerovat AI insighty“ → čerpat tvůj Claude kredit. S heslem si
  dashboard při otevření vyžádá přístup.
- **API klíč patří jen do Secrets**, nikdy do kódu ani do `.env` v gitu.
- Data, která do dashboardu nahraješ, jdou na servery Streamlitu a (při AI
  insightu) k Anthropicu. U citlivých dat zvaž, co nahráváš.

## 📱 Responzivní zobrazení

Dashboard používá široké rozložení a tabulky/grafy přes celou šířku, takže se
škáluje na desktop, tablet i mobil; na úzkém displeji se karty KPI poskládají
pod sebe a postranní panel se schová do menu.

## 🔄 Aktualizace

Po každém pushi do zvolené větve se aplikace **automaticky znovu nasadí**.

## Alternativy

Stejný dashboard zvládnou i **Hugging Face Spaces**, **Render** nebo **Railway** —
postup je obdobný: napoj repo, spouštěcí příkaz `streamlit run src/dashboard.py`,
a tajné hodnoty nastav jako proměnné prostředí / secrets.
