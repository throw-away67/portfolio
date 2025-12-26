from __future__ import annotations

from psycopg import Connection


class CustomerRepository:
    def create(self, conn: Connection, *, full_name: str, email: str | None, phone: str | None, is_vip: bool) -> int:
        cur = conn.execute(
            """
            INSERT INTO customer(full_name, email, phone, is_vip)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (full_name, email, phone, is_vip),
        )
        return int(cur.fetchone()[0])

    def list(self, conn: Connection, limit: int = 50) -> list[dict]:
        cur = conn.execute(
            """
            SELECT id, full_name, email, phone, is_vip, created_at
            FROM customer
            ORDER BY id DESC
            LIMIT %s;
            """,
            (limit,),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]