# Nasazení na Azure App Service (Python + Streamlit)

Tento návod nasadí dashboard na **Azure App Service** (běží na tvém Azure,
profesionální, vlastní doména). Po propojení s GitHubem se každá změna
v `main` nasadí sama (přes GitHub Actions).

> ⚠️ Kroky v Azure portálu musíš udělat přihlášená do svého Azure účtu.
> Kód a konfigurace v repozitáři jsou už připravené (`startup.sh`,
> `requirements.txt`, `src/dashboard.py`).

## 1. Vytvoř Web App
1. Jdi na <https://portal.azure.com> → přihlas se.
2. Nahoře do vyhledávání napiš **App Services** → **Create** → **Web App**.
3. Vyplň:
   - **Resource Group**: vyber existující (klidně stejnou jako panopro-advisor) nebo vytvoř novou.
   - **Name**: např. `panopro-data-analyst` (bude v adrese `…azurewebsites.net`).
   - **Publish**: **Code**
   - **Runtime stack**: **Python 3.12**
   - **Operating System**: **Linux**
   - **Region**: nejbližší (např. West Europe)
   - **Pricing plan**: **B1** (Basic) pro plynulý běh; levnější je **F1 (Free)**, ale usíná a má limity.
4. **Review + create** → **Create**. Počkej na dokončení (~1 min).

## 2. Nastav spouštění (Startup Command)
1. Otevři vytvořenou Web App → vlevo **Configuration** → záložka **General settings**.
2. **Startup Command**: zadej
   ```
   bash startup.sh
   ```
3. **Web sockets**: přepni na **On** (Streamlit je potřebuje).
4. **Always on**: **On** (aby appka neusínala; dostupné na B1 a výš).
5. **Save**.

## 3. Nastav tajné hodnoty (API klíč, heslo)
1. Vlevo **Configuration** → záložka **Application settings** → **New application setting**.
2. Přidej:
   | Name | Value |
   |------|-------|
   | `ANTHROPIC_API_KEY` | tvůj klíč `sk-ant-...` |
   | `APP_PASSWORD` | zvolené heslo (volitelné) |
   | `WEBSITES_PORT` | `8000` |
3. **Save** (appka se restartuje).

## 4. Propoj s GitHubem (automatické nasazení)
1. Vlevo **Deployment Center**.
2. **Source**: **GitHub** → autorizuj → vyber:
   - **Organization**: Traiva2911
   - **Repository**: Data-analyst-claude
   - **Branch**: main
3. **Save**. Azure vytvoří v repozitáři GitHub Actions workflow a spustí první
   nasazení. První build trvá pár minut (instaluje knihovny).

## 5. Otevři appku
- Nahoře na stránce Web App je **Default domain** (adresa `…azurewebsites.net`).
- Klikni na ni → měl by naskočit dashboard. Hotovo! 🎉

---

### Když něco nesedí
- **Application Error / nenaběhne**: zkontroluj **Log stream** (vlevo v menu).
  Nejčastěji chybí Startup Command (`bash startup.sh`) nebo `WEBSITES_PORT=8000`.
- **AI insighty nefungují**: chybí `ANTHROPIC_API_KEY` v Application settings.
- **Build dlouho trvá**: `requirements.txt` obsahuje i `google-ads` (nepovinné pro
  dashboard). Lze ho odebrat pro rychlejší build.
