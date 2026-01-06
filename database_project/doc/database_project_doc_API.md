# Database Project – dokumentace endpointů (Flask)

Aplikace je jednoduchá webová aplikace ve Flasku nad MySQL, která umožňuje:
- přehled zákazníků, produktů a objednávek,
- vytvoření objednávky v transakci (včetně odečtu skladu),
- import zákazníků (CSV) a produktů (JSON),
- základní reporty (přes DB view/join agregace).

## Základní informace

- Framework: Flask
- Databáze: MySQL (přes `pymysql`)
- Spuštění: `python -m src.app` (z kořene `database_project`)
- Konfigurace: `database_project/config/config.yaml`
- Limity uploadu: `app.max_upload_size_mb` → Flask `MAX_CONTENT_LENGTH`
- Všechny endpointy otevírají DB connection per-request přes dekorátor `with_conn`.

### Chyby
- Chyby DB (`DBError`) jsou zachyceny v `with_conn` a vrací se `error.html` s hláškou.
- Velký upload vrací HTTP **413** (`@app.errorhandler(413)`).

---

## Endpointy (routes)

### 1) `GET /`
**Název handleru:** `index(conn)`

**Popis:** Úvodní stránka – přehled zákazníků, produktů a posledních objednávek.

**DB operace:**
- `customers = CustomerRepository.list_all()`
- `products = ProductRepository.list_all()`
- `orders = OrderRepository.list_all()`

**Odpověď:**
- HTML stránka `index.html` s proměnnými:
  - `customers` (list)
  - `products` (list)
  - `orders` (list)

**Status codes:**
- `200` OK
- při DB chybě vykreslí `error.html` (typicky 200, ale s chybovou stránkou)

---

### 2) `GET /customers`
**Název handleru:** `customers(conn)`

**Popis:** Seznam zákazníků (a UI pro import zákazníků přes CSV – import samotný řeší endpoint níže).

**DB operace:**
- `CustomerRepository.list_all()`

**Odpověď:**
- HTML `customers.html` s `customers`

**Status codes:**
- `200` OK

---

### 3) `GET /products`
**Název handleru:** `products(conn)`

**Popis:** Seznam produktů a kategorií (UI může umožnit import produktů přes JSON – import řeší endpoint níže).

**DB operace:**
- `ProductRepository.list_all()`
- `CategoryRepository.list_all()`

**Odpověď:**
- HTML `products.html` s:
  - `products`
  - `categories`

**Status codes:**
- `200` OK

---

### 4) `GET /orders`
**Název handleru:** `orders(conn)`

**Popis:** Seznam všech objednávek.

**DB operace:**
- `OrderRepository.list_all()` (join s customers kvůli `customer_name`)

**Odpověď:**
- HTML `orders.html` s `orders`

**Status codes:**
- `200` OK

---

### 5) `GET /orders/<order_id>`
**Název handleru:** `order_detail(conn, order_id: int)`

**Popis:** Detail konkrétní objednávky, včetně položek a zákazníka.

**Path parametry:**
- `order_id` (int) – ID objednávky

**DB operace:**
- `OrderRepository.get_by_id(order_id)`
- `CustomerRepository.get_by_id(order["customer_id"])`
- `OrderRepository.list_items(order_id)` (join s products kvůli `product_name`)

**Chování při nenalezení:**
- Pokud objednávka neexistuje: `flash("Objednávka #... nebyla nalezena.", "error")` a redirect na `/orders`.

**Odpověď:**
- při úspěchu: HTML `order_detail.html` s:
  - `order`
  - `customer`
  - `items`
- při nenalezení: redirect na `/orders`

**Status codes:**
- `200` OK (detail)
- `302` redirect (nenalezeno)

---

### 6) `GET /orders/new`
**Název handleru:** `order_new(conn)`

**Popis:** Formulář pro vytvoření nové objednávky.

**DB operace (pro vyplnění formuláře):**
- `CustomerRepository.list_all()`
- `ProductRepository.list_all()`

**Odpověď:**
- HTML `order_create.html` s:
  - `customers`
  - `products`

**Status codes:**
- `200` OK

---

### 7) `POST /orders/new`
**Název handleru:** `order_new(conn)` (stejný endpoint, jiná metoda)

**Popis:** Odeslání formuláře pro vytvoření objednávky. Probíhá transakčně přes `OrderService.create_order_transaction()`:
- vytvoření záznamu `orders`,
- vložení `order_items`,
- odečtení skladu z `products.stock`,
- commit/rollback.

**Form data (request.form):**
- `customer_id` (string → int) – povinné, musí být > 0
- `delivery_time` (string | empty) – volitelné; prázdné → `None`
- `product_id` (list) – vícenásobné pole
- `quantity` (list) – vícenásobné pole, párované se `product_id`

**Validace (v handleru):**
- musí být vybrán zákazník a alespoň 1 položka (`items` nesmí být prázdné)
- jinak: flash error a redirect zpět na formulář

**Validace (v `OrderService`):**
- produkt musí existovat a být aktivní (`is_active`)
- `quantity > 0`
- dostatečný sklad (`stock >= qty`)
- jinak vyhodí `OrderServiceError` a provede rollback

**Výsledek:**
- při úspěchu: flash `"Order {order_id} created successfully."` a redirect na `/orders`
- při chybě: flash error a stránka se znovu vykreslí (GET-like návrat na template na konci funkce)

**Status codes:**
- `302` redirect po úspěchu nebo po některých validačních chybách
- `200` pokud dojde k chybě a zůstane se na stránce formuláře

---

### 8) `GET /report`
**Název handleru:** `report(conn)`

**Popis:** Souhrnný report (agregace přes view a další SQL agregace).

**DB operace:**
- `SELECT * FROM view_customer_order_totals ORDER BY total_spent DESC`
- `SELECT * FROM view_product_sales ORDER BY total_revenue DESC`
- agregace přes `orders`:
  - `COUNT(DISTINCT o.id) AS orders_count`
  - `SUM(o.total_amount) AS total_revenue`
  - `MIN(o.total_amount) AS min_order_total`
  - `MAX(o.total_amount) AS max_order_total`

**Odpověď:**
- HTML `report.html` s:
  - `customer_totals`
  - `product_sales`
  - `overall`

**Status codes:**
- `200` OK

---

### 9) `POST /import/customers`
**Název handleru:** `import_customers(conn)`

**Popis:** Import zákazníků z CSV souboru nahraného z formuláře.

**Upload field (request.files):**
- `customers_csv` – povinné

**Konfigurace:**
- Kontroluje se, zda je `"csv"` v `cfg["app"]["allowed_import_formats"]`.
- Pokud není: vrací `error.html` s hláškou „CSV import not allowed by config.“

**Formát CSV:**
- očekávaný header: `name,email,credit,is_active`
- `credit` se parsuje na float
- `is_active`: `true/1/yes` → True, jinak False
- `name` a `email` musí být neprázdné (jinak `CSVImporterError`)

**Chování:**
- pokud soubor chybí: flash error a redirect na `/customers`
- při úspěchu: flash `Imported {count} customers.` a redirect na `/customers`
- při `CSVImporterError`: flash error a redirect na `/customers`

**Status codes:**
- typicky `302` redirect
- při zakázaném importu: `200` s `error.html`
- může vrátit `413` při překročení limitu uploadu

---

### 10) `POST /import/products`
**Název handleru:** `import_products(conn)`

**Popis:** Import produktů z JSON souboru.

**Upload field (request.files):**
- `products_json` – povinné

**Konfigurace:**
- kontroluje se `"json"` v `cfg["app"]["allowed_import_formats"]`
- pokud není: `error.html` s „JSON import not allowed by config.“

**Formát JSON:**
- očekává se pole objektů:
  ```json
  [
    {"name":"Item A","price":10.5,"stock":5,"is_active":true}
  ]
  ```
- validace v importeru:
  - `name` nesmí být prázdné
  - `price > 0`
  - `stock >= 0`

**Chování:**
- pokud soubor chybí: flash error a redirect na `/products`
- při úspěchu: flash `Imported {count} products.` a redirect na `/products`
- při `JSONImporterError`: flash error a redirect na `/products`

**Status codes:**
- typicky `302` redirect
- při zakázaném importu: `200` s `error.html`
- může vrátit `413` při překročení limitu uploadu

---

## Error handler

### `ANY` – HTTP 413 (Payload Too Large)
**Handler:** `file_too_large(_)`

**Popis:** Pokud upload překročí limit `MAX_CONTENT_LENGTH`, vrátí se chybová stránka.

**Odpověď:**
- HTML `error.html`, message: `"Uploaded file too large."`
- HTTP status: `413`

---

## Poznámky pro testování

- UI endpointy jsou HTML (nejde o JSON REST API).
- Importy se testují přes formulář uploadu (multipart/form-data).
- Vytvoření objednávky je transakční: při chybě se provádí rollback a objednávka se nevytvoří.
