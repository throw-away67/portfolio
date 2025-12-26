from __future__ import annotations

import csv
import json
from pathlib import Path

from psycopg import Connection

from .repositories.customer_repo import CustomerRepository
from .repositories.part_repo import PartRepository


class ImportError(Exception):
    pass


def import_customers_csv(conn: Connection, path: str | Path, customer_repo: CustomerRepository) -> int:
    p = Path(path)
    if not p.exists():
        raise ImportError(f"File not found: {p}")

    count = 0
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"full_name", "email", "phone", "is_vip"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ImportError(f"CSV must contain columns: {sorted(required)}")

        for row in reader:
            full_name = (row.get("full_name") or "").strip()
            if not full_name:
                continue
            email = (row.get("email") or "").strip() or None
            phone = (row.get("phone") or "").strip() or None
            is_vip = str(row.get("is_vip", "false")).strip().lower() in {"1", "true", "yes", "ano"}

            customer_repo.create(conn, full_name=full_name, email=email, phone=phone, is_vip=is_vip)
            count += 1
    return count


def import_parts_json(conn: Connection, path: str | Path, part_repo: PartRepository) -> int:
    p = Path(path)
    if not p.exists():
        raise ImportError(f"File not found: {p}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise ImportError(f"Invalid JSON: {e}") from e

    if not isinstance(data, list):
        raise ImportError("JSON must be a list of objects")

    count = 0
    for obj in data:
        if not isinstance(obj, dict):
            continue
        sku = str(obj.get("sku", "")).strip()
        name = str(obj.get("name", "")).strip()
        if not sku or not name:
            continue
        unit_price = float(obj.get("unit_price", 0))
        stock_qty = int(obj.get("stock_qty", 0))
        is_active = bool(obj.get("is_active", True))

        part_repo.upsert_by_sku(
            conn,
            sku=sku,
            name=name,
            unit_price=unit_price,
            stock_qty=stock_qty,
            is_active=is_active,
        )
        count += 1
    return count