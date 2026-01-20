# P2P Bank Node (ESSENTIALS) – prototyp

## Spuštění (Windows, bez IDE)
1) Instalace Python 3.11+ (doporučeno)  
2) Vytvoř v kořeni projektu složky:
- `config/`
- `data/`
- `logs/`

3) Nainstaluj závislosti:
```bash
pip install pyyaml
```

4) Nastav IP v `config/config.yaml` na IP svého PC ve školní síti.

5) Spusť server:
```bash
python -m bank_node
```

Server poslouchá na `TCP <ip>:65525`.

## Ovládání přes PuTTY / telnet
- Připoj se na IP banky a port 65525 (Raw TCP)
- Pošli jeden příkaz (1 řádek, ukončit Enter)

Příklady:
- `BC`
- `AC`
- `AD 10001/<ip> 3000`
- `AB 10001/<ip>`
- `AW 10001/<ip> 2000`
- `AR 10001/<ip>`
- `BA`
- `BN`

## ESSENTIALS proxy
Pro příkazy `AD`, `AW`, `AB`:
- pokud je v příkazu jiný `<ip>` než `bank.ip` v configu, aplikace se připojí na `<ip>:65525` a příkaz přepošle (proxy).

## Persistentní data
Data jsou uložena v `storage.data_file` (JSON). Po restartu aplikace se zůstatky načtou.

## Logování
Logy jsou v `logs/bank.log`:
- příchozí příkaz + klient
- odpověď nebo chyba
- proxy forward a odpověď cílové banky

## Použité zdroje
- Zadání (Moodle): https://moodle.spsejecna.cz/mod/page/view.php?id=11554
- (DOPLNÍŠ) Link na tento chat + promptování

## Znovupoužitý kód (reuse)
1) Konfigurační loader + výjimka:
- původně: `database_project/src/config.py`
  https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/database_project/src/config.py
- použito/upraveno v: `bank_node/config.py`

2) Styl testovacích scénářů v Markdownu (ruční testy):
- inspirace: `database_project/test/scenarios/*.md`
  např. https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/database_project/test/scenarios/3_error_and_config_tests.md
- použito v: `test/scenarios.md`