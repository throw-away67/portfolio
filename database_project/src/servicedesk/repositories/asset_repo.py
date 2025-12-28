from __future__ import annotations

from psycopg import Connection


class AssetRepository:
    def create(
        self,
        conn: Connection,
        *,
        customer_id: int,
        asset_type: str,
        label: str,
        serial_no: str | None,
    ) -> int:
        cur = conn.execute(
            """
            INSERT INTO asset(customer_id, asset_type, label, serial_no)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (customer_id, asset_type, label, serial_no),
        )
        return int(cur.fetchone()[0])

    def list_by_customer(self, conn: Connection, customer_id: int) -> list[dict]:
        cur = conn.execute(
            """
            SELECT id, customer_id, asset_type, label, serial_no, created_at
            FROM asset
            WHERE customer_id = %s
            ORDER BY id DESC;
            """,
            (customer_id,),
        )
        cols = [d. name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def list_all(self, conn: Connection, limit: int = 50) -> list[dict]:
        cur = conn.execute(
            """
            SELECT a.id, a.asset_type, a.label, a.serial_no, a.customer_id, c.full_name AS customer_name, a.created_at
            FROM asset a
            JOIN customer c ON c.id = a.customer_id
            ORDER BY a.id DESC
            LIMIT %s;
            """,
            (limit,),
        )
        cols = [d.name for d in cur. description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]