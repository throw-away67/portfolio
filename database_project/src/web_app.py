from __future__ import annotations

from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash

from servicedesk.config import load_config, ConfigError
from servicedesk.db import Db, DbError
from servicedesk.repositories.asset_repo import AssetRepository
from servicedesk.repositories.customer_repo import CustomerRepository
from servicedesk.repositories.order_part_repo import OrderPartRepository
from servicedesk.repositories.order_repo import OrderRepository
from servicedesk.repositories.part_repo import PartRepository
from servicedesk.repositories.payment_repo import PaymentRepository
from servicedesk.repositories.task_repo import TaskRepository
from servicedesk.services.order_service import (
    CreateOrderPartInput,
    CreateOrderTaskInput,
    OrderService,
    ValidationError,
)
from servicedesk.reports import revenue_report, top_parts
from servicedesk.importers import import_customers_csv, import_parts_json, ImportError

app = Flask(__name__, template_folder="../templates")
app.secret_key = "change-this-secret-key-in-production"

db: Db = None
cfg = None
customer_repo = CustomerRepository()
asset_repo = AssetRepository()
part_repo = PartRepository()
order_repo = OrderRepository()
task_repo = TaskRepository()
order_part_repo = OrderPartRepository()
payment_repo = PaymentRepository()
order_service: OrderService = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/customers")
def customers_list():
    try:
        with db.session() as conn:
            rows = customer_repo.list(conn, limit=100)
        return render_template("customers_list.html", customers=rows)
    except DbError as e:
        flash(f"DB error: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/customers/new", methods=["GET", "POST"])
def customers_new():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        is_vip = request.form.get("is_vip") == "on"

        if not full_name:
            flash("Full name is required", "warning")
            return render_template("customers_new.html")

        try:
            with db.transaction() as conn:
                customer_repo.create(conn, full_name=full_name, email=email, phone=phone, is_vip=is_vip)
            flash("Customer created", "success")
            return redirect(url_for("customers_list"))
        except Exception as e:
            flash(f"Error:  {e}", "danger")

    return render_template("customers_new.html")


@app.route("/parts")
def parts_list():
    try:
        with db.session() as conn:
            rows = part_repo.list(conn, limit=100)
        return render_template("parts_list.html", parts=rows)
    except DbError as e:
        flash(f"DB error:  {e}", "danger")
        return redirect(url_for("index"))


@app.route("/parts/new", methods=["GET", "POST"])
def parts_new():
    if request.method == "POST":
        sku = request.form.get("sku", "").strip()
        name = request.form.get("name", "").strip()
        unit_price = request.form.get("unit_price", "0")
        stock_qty = request.form.get("stock_qty", "0")
        is_active = request.form.get("is_active") == "on"

        if not sku or not name:
            flash("SKU and name are required", "warning")
            return render_template("parts_new.html")

        try:
            with db.transaction() as conn:
                part_repo.upsert_by_sku(
                    conn,
                    sku=sku,
                    name=name,
                    unit_price=float(unit_price),
                    stock_qty=int(stock_qty),
                    is_active=is_active,
                )
            flash("Part created/updated", "success")
            return redirect(url_for("parts_list"))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("parts_new.html")


@app.route("/assets")
def assets_list():
    try:
        with db.session() as conn:
            rows = asset_repo.list_all(conn, limit=100)
        return render_template("assets_list.html", assets=rows)
    except DbError as e:
        flash(f"DB error: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/orders")
def orders_list():
    try:
        with db.session() as conn:
            rows = order_repo.list_totals_view(conn, limit=100)
        return render_template("orders_list.html", orders=rows)
    except DbError as e:
        flash(f"DB error: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/orders/new", methods=["GET", "POST"])
def orders_new():
    if request.method == "POST":
        customer_mode = request.form.get("customer_mode")  # existing / new
        customer_id = None
        full_name = email = phone = None
        is_vip = False

        if customer_mode == "existing":
            customer_id = int(request.form.get("customer_id", 0))
        else:
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip() or None
            phone = request.form.get("phone", "").strip() or None
            is_vip = request.form.get("is_vip") == "on"

        asset_mode = request.form.get("asset_mode")
        asset_id = None
        asset_type = asset_label = asset_serial = None

        if asset_mode == "existing":
            asset_id = int(request.form.get("asset_id", 0))
        else:
            asset_type = request.form.get("asset_type", "").strip()
            asset_label = request.form.get("asset_label", "").strip()
            asset_serial = request.form.get("asset_serial", "").strip() or None

        title = request.form.get("title", "").strip()
        note = request.form.get("note", "").strip() or None

        tasks = []
        i = 0
        while True:
            desc = request.form.get(f"task_desc_{i}", "").strip()
            if not desc:
                break
            hours = float(request.form.get(f"task_hours_{i}", 0))
            rate = request.form.get(f"task_rate_{i}", "").strip()
            rate = float(rate) if rate else cfg.business.default_hourly_rate
            tasks.append(CreateOrderTaskInput(description=desc, hours=hours, hourly_rate=rate))
            i += 1

        parts = []
        j = 0
        while True:
            sku = request.form.get(f"part_sku_{j}", "").strip()
            if not sku:
                break
            qty = int(request.form.get(f"part_qty_{j}", 0))
            parts.append(CreateOrderPartInput(sku=sku, quantity=qty))
            j += 1

        try:
            with db.transaction() as conn:
                order_id = order_service.create_order_full(
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
            flash(f"Order #{order_id} created", "success")
            return redirect(url_for("orders_list"))
        except ValidationError as e:
            flash(f"Validation error: {e}", "warning")
        except Exception as e:
            flash(f"Error:  {e}", "danger")

    try:
        with db.session() as conn:
            customers = customer_repo.list(conn, limit=500)
            assets_all = asset_repo.list_all(conn, limit=500)
            parts_all = part_repo.list(conn, limit=500)
        return render_template(
            "orders_new.html",
            customers=customers,
            assets=assets_all,
            parts=parts_all,
            default_rate=cfg.business.default_hourly_rate,
        )
    except DbError as e:
        flash(f"DB error:  {e}", "danger")
        return redirect(url_for("index"))


@app.route("/orders/<int:order_id>/complete", methods=["GET", "POST"])
def orders_complete(order_id):
    if request.method == "POST":
        amount = float(request.form.get("amount", 0))
        method = request.form.get("method", "cash").strip()
        decrease_stock = request.form.get("decrease_stock") == "on"

        try:
            with db.transaction() as conn:
                payment_id = order_service.complete_order_and_pay(
                    conn,
                    order_id=order_id,
                    payment_amount=amount,
                    payment_method=method,
                    decrease_stock=decrease_stock,
                )
            flash(f"Order #{order_id} completed, payment #{payment_id}", "success")
            return redirect(url_for("orders_list"))
        except ValidationError as e:
            flash(f"Validation error: {e}", "warning")
        except ValueError as e:
            flash(f"Stock error: {e}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    try:
        with db.session() as conn:
            order = order_repo.get_totals_view(conn, order_id)
            if not order:
                flash("Order not found", "warning")
                return redirect(url_for("orders_list"))
            parts_used = order_part_repo.list_for_order(conn, order_id)
        return render_template("orders_complete.html", order=order, parts_used=parts_used)
    except DbError as e:
        flash(f"DB error:  {e}", "danger")
        return redirect(url_for("orders_list"))


@app.route("/reports")
def reports():
    try:
        with db.session() as conn:
            d2 = datetime.now()
            d1 = d2 - timedelta(days=30)
            rev = revenue_report(conn, d1, d2)
            tops = top_parts(conn, limit=10)
        return render_template("reports.html", revenue=rev, top_parts=tops)
    except DbError as e:
        flash(f"DB error: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/import", methods=["GET", "POST"])
def import_data():
    if request.method == "POST":
        mode = request.form.get("mode")  # customers / parts
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("No file selected", "warning")
            return render_template("import. html")

        import tempfile
        import os

        fd, path = tempfile.mkstemp()
        try:
            file.save(path)

            if mode == "customers":
                with db.transaction() as conn:
                    n = import_customers_csv(conn, path, customer_repo)
                flash(f"Imported {n} customers", "success")
            elif mode == "parts":
                with db.transaction() as conn:
                    n = import_parts_json(conn, path, part_repo)
                flash(f"Imported {n} parts", "success")
            else:
                flash("Unknown import mode", "warning")
        except ImportError as e:
            flash(f"Import error: {e}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            os.close(fd)
            os.unlink(path)

        return redirect(url_for("import_data"))

    return render_template("import.html")


if __name__ == "__main__":
    try:
        cfg = load_config("config.toml")
        db = Db(cfg.db)
        order_service = OrderService(
            customer_repo=customer_repo,
            asset_repo=asset_repo,
            part_repo=part_repo,
            order_repo=order_repo,
            task_repo=task_repo,
            order_part_repo=order_part_repo,
            payment_repo=payment_repo,
        )
        app.run(debug=True, host="127.0.0.1", port=5000)
    except ConfigError as e:
        print(f"[CONFIG ERROR] {e}")
        raise SystemExit(2)
