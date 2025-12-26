# ServiceDesk (D1) – Python + PostgreSQL (CLI)

## Požadavky
- Python 3.11+
- PostgreSQL 13+ (lokálně)
- vytvořená databáze `servicedesk`

## Instalace
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

## Nastavení databáze
1) V PostgreSQL vytvoř DB:
```sql
CREATE DATABASE servicedesk;
```

2) Uprav `config.toml` (host/user/password/dbname).

3) Import struktury:
```bash
psql -h localhost -U postgres -d servicedesk -f db/ddl.sql
psql -h localhost -U postgres -d servicedesk -f db/views.sql
psql -h localhost -U postgres -d servicedesk -f db/seed.sql
```

## Spuštění aplikace
```bash
python src/main.py
```

## Import dat
V CLI:
- `6) Import customers CSV` použij `testdata/customers.csv`
- `7) Import parts JSON` použij `testdata/parts.json`