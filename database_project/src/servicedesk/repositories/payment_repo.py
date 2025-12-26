from __future__ import annotations

from psycopg import Connection


class PaymentRepository:
    def create(self, conn: Connection, *, order_id: int, amount: float, method: str, is_refund: bool = False) -> int:
        cur = conn.execute(
            """
            INSERT INTO payment(order_id, amount, method, is_refund)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (order_id, amount, method, is_refund),
        )
        return int(cur.fetchone()[0])