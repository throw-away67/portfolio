from __future__ import annotations

from datetime import datetime

from psycopg import Connection


def revenue_report(conn: Connection, date_from: datetime, date_to: datetime) -> dict:
    # joins: payment + service_order + order_part + part (and tasks indirectly via view if needed)
    cur = conn.execute(
        """
        SELECT
          COUNT(DISTINCT o.id) AS orders_count,
          COALESCE(SUM(p.amount), 0) AS payments_sum,
          COALESCE(SUM(op.quantity * op.unit_price), 0) AS parts_sum,
          COALESCE(SUM(st.hours), 0) AS total_hours
        FROM service_order o
        LEFT JOIN payment p ON p.order_id = o.id AND p.is_refund = false
        LEFT JOIN order_part op ON op.order_id = o.id
        LEFT JOIN service_task st ON st.order_id = o.id
        WHERE o.created_at >= %s AND o.created_at < %s;
        """,
        (date_from, date_to),
    )
    row = cur.fetchone()
    cols = [d.name for d in cur.description]
    return dict(zip(cols, row))


def top_parts(conn: Connection, limit: int = 10) -> list[dict]:
    cur = conn.execute(
        """
        SELECT
          pr.sku,
          pr.name,
          SUM(op.quantity) AS total_qty,
          SUM(op.quantity * op.unit_price) AS total_value
        FROM order_part op
        JOIN part pr ON pr.id = op.part_id
        GROUP BY pr.sku, pr.name
        ORDER BY total_qty DESC
        LIMIT %s;
        """,
        (limit,),
    )
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]