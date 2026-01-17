# Testovací scénář 1 – Instalace a nastavení

Cíl: Ověřit, že aplikaci lze nainstalovat a spustit na školním PC, včetně importu DB.

## Předpoklady
- Přístup k MySQL serveru
- Python 3.10+, pip, možnost vytvořit virtualenv
- Síťová konektivita (pokud DB běží externě)

## Kroky
1. Stažení projektu z Git (portfolio). cd database_project
2. Vytvoření virtualenv:
   - `python -m venv .venv`
   - Aktivace: Windows `.\.venv\Scripts\activate`, Linux/Mac `source .venv/bin/activate`
3. Instalace závislostí:
   - `pip install -r requirements.txt`
4. Nastavení `config/config.yaml`:
   - Vyplnit `database.host`, `port`, `user`, `password`, `name`
5. Import DB schématu:
   - `mysql -u <user> -p -h <host> -P <port> < db/schema.sql`
6. Import seed dat:
   - `mysql -u <user> -p -h <host> -P <port> portfolio_app < db/seed.sql`
7. Spuštění aplikace:
   - `python src/app.py`
   - Otevřít `http://127.0.0.1:5000/`
8. Ověření UI:
   - Domovská stránka zobrazuje zákazníky, produkty, objednávky (prázdná či dle seed)
9. Kontrola konfiguračních chyb:
   - Dočasně zneplatnit config (např. smazat `database.name`) → zobrazí se chybová stránka s popisem problému.

## Očekávaný výsledek
- Aplikace běží, DB schema a seed jsou importovány, UI je funkční.
