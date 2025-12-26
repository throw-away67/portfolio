from __future__ import annotations

from psycopg import Connection


class OrderPartRepository:
    def add_part(self, conn: Connection, *, order_id: int, part_id: int, quantity: int, unit_price: float) -> None:
        conn.execute(
            """
            INSERT INTO order_part(order_id, part_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (order_id, part_id) DO UPDATE SET
              quantity = order_part.quantity + EXCLUDED.quantity;
            """,
            (order_id, part_id, quantity, unit_price),
        )

    def list_for_order(self, conn: Connection, order_id: int) -> list[dict]:
        cur = conn.execute(
            """
            SELECT op.order_id, op.part_id, p.sku, p.name, op.quantity, op.unit_price
            FROM order_part op
            JOIN part p ON p.id = op.part_id
            WHERE op.order_id = %s
            ORDER BY p.name;
            """,
            (order_id,),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]