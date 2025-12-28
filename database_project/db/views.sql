BEGIN;

CREATE OR REPLACE VIEW v_order_totals AS
SELECT
  o.id AS order_id,
  o.status,
  o.created_at,
  o.completed_at,
  c.id AS customer_id,
  c.full_name AS customer_name,
  a.label AS asset_label,

  COALESCE(t.task_cost, 0) AS labor_total,
  COALESCE(p.parts_cost, 0) AS parts_total,
  (COALESCE(t.task_cost, 0) + COALESCE(p.parts_cost, 0)) AS grand_total
FROM service_order o
JOIN customer c ON c.id = o.customer_id
JOIN asset a ON a.id = o.asset_id
LEFT JOIN (
  SELECT order_id, SUM(hours * hourly_rate) AS task_cost
  FROM service_task
  GROUP BY order_id
) t ON t.order_id = o.id
LEFT JOIN (
  SELECT order_id, SUM(quantity * unit_price) AS parts_cost
  FROM order_part
  GROUP BY order_id
) p ON p.order_id = o.id;

CREATE OR REPLACE VIEW v_customer_activity AS
SELECT
  c.id AS customer_id,
  c.full_name,
  c.email,
  c.is_vip,
  COUNT(o.id) AS orders_count,
  MAX(o.created_at) AS last_order_at,
  COALESCE(SUM(v.grand_total), 0) AS total_spent
FROM customer c
LEFT JOIN service_order o ON o.customer_id = c.id
LEFT JOIN v_order_totals v ON v.order_id = o.id
GROUP BY c.id, c.full_name, c.email, c.is_vip;

COMMIT;