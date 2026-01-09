# Testovací scénář 2 – Funkční testy

Cíl: Otestovat splnění bodů 4–7 (CRUD přes více tabulek, transakce, report, import).

## Předpoklady
- Aplikace spuštěna, DB připravena dle scénáře 1.

## Kroky
### A. Vytvoření objednávky (CRUD + transakce)
1. Otevřít `/orders/new`.
2. Vybrat existujícího zákazníka.
3. Přidat minimálně 2 položky:
   - Produkt A (množství 2)
   - Produkt B (množství 1)
4. Odeslat objednávku.
5. Ověřit:
   - V / na domovské stránce se objednávka zobrazuje.
   - Sklad produktů se adekvátně snížil.
   - Celková částka odpovídá součtům položek.
6. Chybové větve:
   - Pokus objednat více kusů než je sklad → aplikace zobrazí chybu a nic neuloží (rollback).

### B. Report (/report)
1. Otevřít `/report`.
2. Ověřit:
   - Tabulka "Top zákazníci dle útraty" – agregace (COUNT, SUM).
   - Tabulka "Prodeje produktů" – agregace z `order_items`.
   - "Celkové statistiky" – COUNT, SUM, MIN, MAX z `orders`.

### C. Import dat (CSV/JSON)
***můžete použít soubory z tohoto repozitáře /database_project/test/data***
1. Import zákazníků (CSV) na `/customers`:
   - Připravit CSV soubor s hlavičkou `name,email,credit,is_active`.
   - Nahrát a odeslat.
   - Ověřit přidání záznamů do tabulky `customers`.
2. Import produktů (JSON) na `/products`:
   - Připravit JSON pole objektů se strukturou:
     ```
     [{"name":"Item1","price":10.5,"stock":5,"is_active":true}, ...]
     ```
   - Nahrát a odeslat.
   - Ověřit přidání záznamů do `products`.

## Očekávané výsledky
- Objednávka se vytvoří v jedné transakci (orders + order_items + update stock).
- Report zobrazuje smysluplná agregovaná data ze tří a více tabulek.
- Import CSV/JSON probíhá s validací a hláškami.
