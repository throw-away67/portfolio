# PV – P2P Bank Node (ESSENTIALS) – návrh řešení

Datum: 2026-01-17  
Autor: Profex993  
Repo (portfolio): throw-away67/portfolio  
Cílová obtížnost: **ESSENTIALS BANK NODE** (proxy pro `AD/AW/AB`)

---

## 1) Cíl projektu
Cílem je navrhnout bankovní node v P2P síti, který bude představovat jednu banku ve školní síti. Node bude komunikovat přes TCP/IP pomocí přesně definovaných textových příkazů a bude ho možné ovládat přes PuTTY/telnet.

Důležité cíle (podle zadání):
- korektní implementace protokolu,
- timeouty (klíčová část),
- logování,
- ukládání dat (neztratit účty po restartu),
- schopnost znovu použít vlastní kód z portfolia.

---

## 2) Funkční požadavky (protokol)
Zprávy jsou jednořádkové (ukončené `\n`), v UTF‑8. Na každý příkaz musí přijít odpověď.

Podporované příkazy:
- `BC` → `BC <ip>`
- `AC` → `AC <account>/<ip>`
- `AD <account>/<ip> <number>` → `AD`
- `AW <account>/<ip> <number>` → `AW`
- `AB <account>/<ip>` → `AB <number>`
- `AR <account>/<ip>` → `AR`
- `BA` → `BA <number>`
- `BN` → `BN <number>`

Chyby:
- `ER <message>` (jedna věta, česky nebo anglicky)

Formáty:
- `<ip>`: IPv4 ve tvaru `x.x.x.x` (kód banky)
- `<account>`: 10000–99999
- `<number>`: 0..9223372036854775807

---

## 3) ESSENTIALS rozšíření (proxy)
U příkazů `AD`, `AW`, `AB` musí aplikace fungovat jako proxy, pokud dostane jiný kód banky než vlastní IP.

Princip:
1) pokud příkaz `AD/AW/AB` obsahuje `<ip>` jiné banky než `bank.ip`,
2) node se připojí na `<ip>:65525`,
3) pošle stejný textový příkaz,
4) přečte 1 řádek odpovědi,
5) odpověď vrátí původnímu klientovi.

Poznámka: Pro účely třídy předpokládám sjednocený port **65525** pro všechny banky, aby proxy šla dělat jen podle IP.

---

## 4) Nefunkční požadavky

### 4.1 Síť a prostředí
- Běh na Windows (školní PC).
- TCP server na portu v rozsahu 65525–65535 (navržený default 65525).
- Ovládání přes PuTTY/telnet, neimplementuje se klient.

### 4.2 Paralelní klienti
- Node musí zvládnout více připojení současně.
- Návrh pro prototyp: `thread-per-connection` (pro každého klienta vlastní vlákno).

### 4.3 Timeouty
Timeouty jsou požadované a zásadní. Budou konfigurovatelné:
- `proxy_timeout_sec` (default 5 s) – connect i čekání na odpověď při proxy
- `client_idle_timeout_sec` (např. 60 s) – maximální neaktivita klienta v otevřeném spojení (důležité pro ruční psaní v PuTTY)

Pokud timeout nastane, spojení se ukončí a do logu se zapíše důvod (případně se vrátí `ER` u proxy chyb).

### 4.4 Logování
Aplikace bude logovat:
- připojení/odpojení klienta,
- příchozí příkazy a odpovědi,
- chyby a důvody (invalid příkaz, špatný formát, nedostatek prostředků, timeout),
- proxy komunikaci (kam se připojila a jaká odpověď přišla).

Log bude do souboru + volitelně do konzole.

### 4.5 Persistence (neztratit data po restartu)
- Stav účtů a zůstatků bude uložen v souboru (navržený formát JSON).
- Ukládání bude atomické (temp + replace), aby se minimalizovalo riziko poškození dat při pádu aplikace.

---

## 5) Návrh architektury a komponent

### 5.1 Komponenty
1) **TCP server**
- bind na `bank.ip:bank.port`
- accept loop
- pro každé spojení spustí handler

2) **Client handler**
- čte příkazy po řádcích (newline-delimited)
- zpracovává více příkazů v jednom spojení (dokud se klient neodpojí nebo nenastane idle timeout)
- na každý příkaz odešle jednu odpověď

3) **Parser/Validator protokolu**
- převede text na interní strukturu příkazu
- validuje formáty a rozsahy
- při chybě vrací `ER ...`

4) **Doménová logika banky (účty)**
- create / deposit / withdraw / balance / remove / total / count
- synchronizace zámkem (kvůli paralelním klientům)
- po změně uloží stav do persistence

5) **Persistence vrstva**
- načte data při startu
- ukládá data po změnách

6) **Proxy klient**
- při cizí IP (jen AD/AW/AB) forwarduje příkaz a vrací odpověď
- má vlastní timeout

7) **Logging**
- jednotný logger pro všechny části

### 5.2 Datový model (návrh)
- Účty: `account_number -> balance`
- `account_number` je int 10000–99999
- `balance` je int >= 0

Persistovaný formát (návrh):
```json
{
  "accounts": {
    "12345": 1000,
    "54321": 0
  }
}
```

---

## 6) Diagramy
Diagramy jsou připravené jako PlantUML soubory ve složce:
- `./diagrams`

---

## 7) Konfigurace (návrh)
Konfigurace bude v YAML a bude obsahovat minimálně:
- `bank.ip` (ručně zadaná IP banky)
- `bank.port` (default 65525)
- `timeouts.client_idle_timeout_sec`
- `timeouts.proxy_timeout_sec`
- `storage.data_file`
- `logging.file`, `logging.level`

---

## 8) Testovací plán (návrh)
Testování bude probíhat ručně přes PuTTY/telnet:
- smoke test `BC`
- `AC` založení účtu
- `AD/AB/AW` běžné operace
- chyby formátu (neznámý příkaz, špatný account/amount)
- `AR` pouze při zůstatku 0
- `BA`, `BN`
- persistence: restart a kontrola zůstatku
- proxy: `AD/AW/AB` na cizí IP

Konkrétní scénáře budou ve složce:
- `./test/scenarios.md`

---

## 9) Plán znovupoužití kódu (reuse) – knihovny
Chci znovu použít části svého portfolia tak, aby z nich vznikly malé interní knihovny (a šly použít i příště).

### 9.1 `pvl_config` (konfigurace)
Znovupoužitý základ: YAML config loader a validační pattern.

- Zdroj: `database_project/src/config.py`  
  https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/database_project/src/config.py

### 9.2 `pvl_cli` (CLI argumenty)
Znovupoužitý pattern: oddělený `build_parser()` přes argparse.

- Zdroj: `downloader/cli.py`  
  https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/downloader/cli.py

### 9.3 `pvl_persist` (práce se soubory)
Znovupoužitý pattern: načtení stavu ze souboru při startu + ukládání změn.

- Zdroj (pattern): `crawler/main.py`  
  https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/crawler/main.py#L18-L32

### 9.4 Dokumentační testy (scénáře)
Znovupoužitý formát strukturovaných testovacích scénářů v Markdownu.

- Zdroj: `database_project/test/scenarios/*.md`  
  např. https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/database_project/test/scenarios/3_error_and_config_tests.md

---

## 10) Použité zdroje (bude doplněno)
- Zadání (Moodle): https://moodle.spsejecna.cz/mod/page/view.php?id=11554
- (doplním) odkaz na rozhovor s AI + promptování