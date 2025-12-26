-- ServiceDesk (D1 - Repository pattern)
-- PostgreSQL DDL: tables, types, constraints

BEGIN;

-- Clean (for re-import during testing)
DROP VIEW IF EXISTS v_customer_activity;
DROP VIEW IF EXISTS v_order_totals;

DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_part;
DROP TABLE IF EXISTS service_task;
DROP TABLE IF EXISTS service_order;
DROP TABLE IF EXISTS part;
DROP TABLE IF EXISTS asset;
DROP TABLE IF EXISTS customer;

DROP TYPE IF EXISTS order_status;

-- ENUM (DTypes: enum)
CREATE TYPE order_status AS ENUM ('new', 'in_progress', 'done', 'cancelled');

-- CUSTOMER (string, bool)
CREATE TABLE customer (
  id            BIGSERIAL PRIMARY KEY,
  full_name     VARCHAR(200) NOT NULL,
  email         VARCHAR(320),
  phone         VARCHAR(50),
  is_vip        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_customer_email UNIQUE (email)
);

-- ASSET (string)
CREATE TABLE asset (
  id            BIGSERIAL PRIMARY KEY,
  customer_id   BIGINT NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
  asset_type    VARCHAR(50) NOT NULL,          -- e.g. 'pc', 'car', 'bike'
  label         VARCHAR(200) NOT NULL,         -- e.g. "Lenovo T480", "Octavia 2.0 TDI"
  serial_no     VARCHAR(100),                  -- can be VIN / SN
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- PART (float numeric, string, int)
CREATE TABLE part (
  id            BIGSERIAL PRIMARY KEY,
  sku           VARCHAR(64) NOT NULL,
  name          VARCHAR(200) NOT NULL,
  unit_price    NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
  stock_qty     INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_part_sku UNIQUE (sku)
);

-- SERVICE ORDER (enum, datetime)
CREATE TABLE service_order (
  id            BIGSERIAL PRIMARY KEY,
  customer_id   BIGINT NOT NULL REFERENCES customer(id),
  asset_id      BIGINT NOT NULL REFERENCES asset(id),
  status        order_status NOT NULL DEFAULT 'new',
  title         VARCHAR(200) NOT NULL,
  note          TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at  TIMESTAMPTZ
);

-- TASKS (float numeric)
CREATE TABLE service_task (
  id            BIGSERIAL PRIMARY KEY,
  order_id      BIGINT NOT NULL REFERENCES service_order(id) ON DELETE CASCADE,
  description   VARCHAR(300) NOT NULL,
  hours         NUMERIC(6,2) NOT NULL CHECK (hours >= 0),
  hourly_rate   NUMERIC(10,2) NOT NULL CHECK (hourly_rate >= 0)
);

-- M:N (order <-> part)
CREATE TABLE order_part (
  order_id      BIGINT NOT NULL REFERENCES service_order(id) ON DELETE CASCADE,
  part_id       BIGINT NOT NULL REFERENCES part(id),
  quantity      INTEGER NOT NULL CHECK (quantity > 0),
  unit_price    NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0), -- price snapshot at time of order
  PRIMARY KEY (order_id, part_id)
);

-- PAYMENT (float numeric, bool, datetime)
CREATE TABLE payment (
  id            BIGSERIAL PRIMARY KEY,
  order_id      BIGINT NOT NULL REFERENCES service_order(id) ON DELETE CASCADE,
  amount        NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
  paid_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  method        VARCHAR(30) NOT NULL DEFAULT 'cash', -- cash/card/transfer
  is_refund     BOOLEAN NOT NULL DEFAULT FALSE
);

COMMIT;