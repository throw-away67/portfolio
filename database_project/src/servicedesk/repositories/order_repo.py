from __future__ import annotations

from psycopg import Connection


class OrderRepository:
    def create(self, conn: Connection, *, customer_id: int, asset_id: int, title: str, note: str | None) -> int:
        cur = conn.execute(
            """
            INSERT INTO service_order(customer_id, asset_id, title, note)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (customer_id, asset_id, title, note),
        )
        return int(cur.fetchone()[0])

    def set_status(self, conn: Connection, *, order_id: int, status: str) -> None:
        conn.execute(
            "UPDATE service_order SET status = %s WHERE id = %s;",
            (status, order_id),
        )

    def complete(self, conn: Connection, *, order_id: int) -> None:
        conn.execute(
            """
            UPDATE service_order
            SET status = 'done', completed_at = now()
            WHERE id = %s;
            """,
            (order_id,),
        )

    def get_totals_view(self, conn: Connection, order_id: int) -> dict | None:
        cur = conn.execute("SELECT * FROM v_order_totals WHERE order_id = %s;", (order_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [d.name for d in cur.description]
        return dict(zip(cols, row))

    def list_totals_view(self, conn: Connection, limit: int = 30) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM v_order_totals ORDER BY order_id DESC LIMIT %s;",
            (limit,),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]