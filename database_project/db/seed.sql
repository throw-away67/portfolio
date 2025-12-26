BEGIN;

INSERT INTO customer(full_name, email, phone, is_vip)
VALUES
('Jan Novak', 'jan.novak@example.com', '+420777111222', false),
('Petr Svoboda', 'petr.svoboda@example.com', '+420777333444', true);

INSERT INTO asset(customer_id, asset_type, label, serial_no)
VALUES
(1, 'pc', 'Lenovo ThinkPad T480', 'SN-T480-001'),
(2, 'car', 'Skoda Octavia 2.0 TDI', 'VIN-ABC-123');

INSERT INTO part(sku, name, unit_price, stock_qty)
VALUES
('RAM-16GB', 'DDR4 RAM 16GB', 899.00, 10),
('SSD-1TB', 'SSD 1TB', 1790.00, 5),
('OIL-5W30', 'Motor oil 5W-30 1L', 249.00, 30);

COMMIT;