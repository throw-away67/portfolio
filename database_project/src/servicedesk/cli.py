from __future__ import annotations

from datetime import datetime, timedelta

from .db import Db
from .importers import import_customers_csv, import_parts_json
from .repositories.asset_repo import AssetRepository
from .repositories.customer_repo import CustomerRepository
from .repositories.order_part_repo import OrderPartRepository
from .repositories.order_repo import OrderRepository
from .repositories.part_repo import PartRepository
from .repositories.payment_repo import PaymentRepository
from .repositories.task_repo import TaskRepository
from .reports import revenue_report, top_parts
from .services.order_service import CreateOrderPartInput, CreateOrderTaskInput, OrderService, ValidationError


def _prompt(msg: str) -> str:
    return input(msg).strip()


def run_cli(db: Db, default_hourly_rate: float) -> None:
    customer_repo = CustomerRepository()
    asset_repo = AssetRepository()
    part_repo = PartRepository()
    order_repo = OrderRepository()
    task_repo = TaskRepository()
    order_part_repo = OrderPartRepository()
    payment_repo = PaymentRepository()

    service = OrderService(
        customer_repo=customer_repo,
        asset_repo=asset_repo,
        part_repo=part_repo,
        order_repo=order_repo,
        task_repo=task_repo,
        order_part_repo=order_part_repo,
        payment_repo=payment_repo,
    )

    while True:
        print("\n=== ServiceDesk CLI ===")
        print("1) List customers")
        print("2) List parts (stock)")
        print("3) Create order (multi-table)")
        print("4) Complete order + pay (transaction)")
        print("5) List order totals (view)")
        print("6) Import customers CSV")
        print("7) Import parts JSON")
        print("8) Report revenue + top parts")
        print("0) Exit")

        choice = _prompt("> ")
        try:
            if choice == "0":
                return

            elif choice == "1":
                with db.session() as conn:
                    rows = customer_repo.list(conn, limit=50)
                for r in rows:
                    print(f'#{r["id"]} {r["full_name"]} email={r["email"]} vip={r["is_vip"]}')

            elif choice == "2":
                with db.session() as conn:
                    rows = part_repo.list(conn, limit=50)
                for r in rows:
                    print(f'#{r["id"]} {r["sku"]} {r["name"]} price={r["unit_price"]} stock={r["stock_qty"]}')

            elif choice == "3":
                # create order in a single DB transaction (safe for partial inserts)
                print("\nCreate order - choose customer:")
                print("A) Existing customer_id")
                print("B) New customer")
                mode = _prompt("A/B: ").upper()

                customer_id = None
                full_name = email = phone = None
                is_vip = False

                if mode == "A":
                    customer_id = int(_prompt("customer_id: "))
                else:
                    full_name = _prompt("full_name: ")
                    email = _prompt("email (optional): ") or None
                    phone = _prompt("phone (optional): ") or None
                    is_vip = _prompt("is_vip (yes/no): ").lower() in {"yes", "ano", "y", "1", "true"}

                print("\nChoose asset:")
                print("A) Existing asset_id")
                print("B) New asset")
                amode = _prompt("A/B: ").upper()
                asset_id = None
                asset_type = asset_label = asset_serial = None
                if amode == "A":
                    asset_id = int(_prompt("asset_id: "))
                else:
                    asset_type = _prompt("asset_type (pc/car/bike): ")
                    asset_label = _prompt("label: ")
                    asset_serial = _prompt("serial_no (optional): ") or None

                title = _prompt("order title: ")
                note = _prompt("note (optional): ") or None

                tasks: list[CreateOrderTaskInput] = []
                while True:
                    add = _prompt("Add task? (y/n): ").lower()
                    if add != "y":
                        break
                    desc = _prompt("  task desc: ")
                    hours = float(_prompt("  hours: "))
                    rate_in = _prompt(f"  hourly_rate (default {default_hourly_rate}): ")
                    rate = float(rate_in) if rate_in else float(default_hourly_rate)
                    tasks.append(CreateOrderTaskInput(description=desc, hours=hours, hourly_rate=rate))

                parts: list[CreateOrderPartInput] = []
                while True:
                    add = _prompt("Add part by SKU? (y/n): ").lower()
                    if add != "y":
                        break
                    sku = _prompt("  SKU: ")
                    qty = int(_prompt("  quantity: "))
                    parts.append(CreateOrderPartInput(sku=sku, quantity=qty))

                with db.transaction() as conn:
                    order_id = service.create_order_full(
                        conn,
                        customer_id=customer_id,
                        customer_full_name=full_name,
                        customer_email=email,
                        customer_phone=phone,
                        is_vip=is_vip,
                        asset_id=asset_id,
                        asset_type=asset_type,
                        asset_label=asset_label,
                        asset_serial_no=asset_serial,
                        title=title,
                        note=note,
                        tasks=tasks,
                        parts=parts,
                    )
                print(f"Created order_id={order_id}")

            elif choice == "4":
                order_id = int(_prompt("order_id: "))
                amount = float(_prompt("payment amount: "))
                method = _prompt("method (cash/card/transfer): ") or "cash"

                # Transaction over multiple tables: order + payment + stock decrease
                with db.transaction() as conn:
                    payment_id = service.complete_order_and_pay(
                        conn,
                        order_id=order_id,
                        payment_amount=amount,
                        payment_method=method,
                        decrease_stock=True,
                    )
                print(f"Order completed. payment_id={payment_id}")

            elif choice == "5":
                with db.session() as conn:
                    rows = order_repo.list_totals_view(conn, limit=30)
                for r in rows:
                    print(
                        f'order#{r["order_id"]} status={r["status"]} customer={r["customer_name"]} '
                        f'labor={r["labor_total"]} parts={r["parts_total"]} total={r["grand_total"]}'
                    )

            elif choice == "6":
                path = _prompt("path to customers.csv: ")
                with db.transaction() as conn:
                    n = import_customers_csv(conn, path, customer_repo)
                print(f"Imported customers: {n}")

            elif choice == "7":
                path = _prompt("path to parts.json: ")
                with db.transaction() as conn:
                    n = import_parts_json(conn, path, part_repo)
                print(f"Imported/updated parts: {n}")

            elif choice == "8":
                with db.session() as conn:
                    d2 = datetime.now()
                    d1 = d2 - timedelta(days=30)
                    rep = revenue_report(conn, d1, d2)
                    tops = top_parts(conn, limit=10)
                print(f"Revenue report (last 30 days): {rep}")
                print("Top parts:")
                for t in tops:
                    print(f'  {t["sku"]} {t["name"]} qty={t["total_qty"]} value={t["total_value"]}')

            else:
                print("Unknown choice.")

        except ValidationError as e:
            print(f"[INPUT ERROR] {e}")
        except ValueError as e:
            print(f"[VALUE ERROR] {e}")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")