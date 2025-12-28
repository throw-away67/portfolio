from __future__ import annotations

from psycopg import Connection


class PartRepository:
    def upsert_by_sku(self, conn: Connection, *, sku: str, name: str, unit_price: float, stock_qty: int, is_active: bool = True) -> int:
        cur = conn.execute(
            """
            INSERT INTO part(sku, name, unit_price, stock_qty, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (sku) DO UPDATE SET
              name = EXCLUDED.name,
              unit_price = EXCLUDED.unit_price,
              stock_qty = EXCLUDED.stock_qty,
              is_active = EXCLUDED.is_active
            RETURNING id;
            """,
            (sku, name, unit_price, stock_qty, is_active),
        )
        return int(cur.fetchone()[0])

    def get_by_sku(self, conn: Connection, sku: str) -> dict | None:
        cur = conn.execute(
            """
            SELECT id, sku, name, unit_price, stock_qty, is_active, created_at
            FROM part WHERE sku = %s;
            """,
            (sku,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d.name for d in cur.description]
        return dict(zip(cols, row))

    def list(self, conn: Connection, limit: int = 50) -> list[dict]:
        cur = conn.execute(
            """
            SELECT id, sku, name, unit_price, stock_qty, is_active, created_at
            FROM part
            ORDER BY id DESC
            LIMIT %s;
            """,
            (limit,),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def decrease_stock(self, conn: Connection, *, part_id: int, qty: int) -> None:
        cur = conn.execute(
            """
            UPDATE part
            SET stock_qty = stock_qty - %s
            WHERE id = %s AND stock_qty >= %s;
            """,
            (qty, part_id, qty),
        )
        if cur.rowcount != 1:
            raise ValueError("Not enough stock for part_id=%s" % part_id)