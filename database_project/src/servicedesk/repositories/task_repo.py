from __future__ import annotations

from psycopg import Connection


class TaskRepository:
    def create(self, conn: Connection, *, order_id: int, description: str, hours: float, hourly_rate: float) -> int:
        cur = conn.execute(
            """
            INSERT INTO service_task(order_id, description, hours, hourly_rate)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (order_id, description, hours, hourly_rate),
        )
        return int(cur.fetchone()[0])