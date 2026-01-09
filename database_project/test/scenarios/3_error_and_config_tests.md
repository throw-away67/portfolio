# Testovací scénář 3 – Testy chyb a konfigurace

Cíl: Otestovat robustní chování aplikace při chybách konfigurace, vstupů a DB připojení.

## Předpoklady
- Aplikace spuštěna, tester má možnost upravit `config.yaml`.

## Kroky
### A. Konfigurační chyby
1. Odstranit `database.name` z `config/config.yaml`.
2. Spustit aplikaci.
3. Očekávat: zobrazení chybové stránky s informací o chybě konfigurace.

### B. Limit velikosti uploadu
1. Nastavit `app.max_upload_size_mb` na 1.
2. Zkusit nahrát JSON/CSV soubor > 1 MB.
3. Očekávat: HTTP 413 (soubor příliš velký) a chybová stránka.

### C. Chybné CSV/JSON
1. CSV bez `email` nebo s prázdným `name`:
   - Očekávat: chybová hláška a žádná změna v DB (rollback).
2. JSON, který není pole, nebo má neplatná data (`price <= 0`, `stock < 0`):
   - Očekávat: chybová hláška.

### D. Chybné objednávky
1. Objednat produkt s množstvím 0 nebo záporným:
   - Očekávat: chybová hláška, bez změny v DB.
2. Objednat více kusů než skladem:
   - Očekávat: chybová hláška, bez změny v DB.

### E. DB připojení
1. Nastavit špatné `database.password`.
2. Spustit aplikaci a přejít na `/`:
   - Očekávat: chybová stránka (DB error).

## Očekávané výsledky
- Aplikace ve všech případech reaguje rozumně, informuje uživatele a neprovádí nekonzistentní změny.
