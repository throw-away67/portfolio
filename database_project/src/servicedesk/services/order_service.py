from __future__ import annotations

from dataclasses import dataclass

from psycopg import Connection

from ..repositories.asset_repo import AssetRepository
from ..repositories.customer_repo import CustomerRepository
from ..repositories.order_part_repo import OrderPartRepository
from ..repositories.order_repo import OrderRepository
from ..repositories.part_repo import PartRepository
from ..repositories.payment_repo import PaymentRepository
from ..repositories.task_repo import TaskRepository


class ValidationError(Exception):
    pass


@dataclass
class CreateOrderTaskInput:
    description: str
    hours: float
    hourly_rate: float


@dataclass
class CreateOrderPartInput:
    sku: str
    quantity: int


class OrderService:
    def __init__(
        self,
        *,
        customer_repo: CustomerRepository,
        asset_repo: AssetRepository,
        part_repo: PartRepository,
        order_repo: OrderRepository,
        task_repo: TaskRepository,
        order_part_repo: OrderPartRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self.customer_repo = customer_repo
        self.asset_repo = asset_repo
        self.part_repo = part_repo
        self.order_repo = order_repo
        self.task_repo = task_repo
        self.order_part_repo = order_part_repo
        self.payment_repo = payment_repo

    def create_order_full(
        self,
        conn: Connection,
        *,
        customer_id: int | None,
        customer_full_name: str | None,
        customer_email: str | None,
        customer_phone: str | None,
        is_vip: bool,
        asset_id: int | None,
        asset_type: str | None,
        asset_label: str | None,
        asset_serial_no: str | None,
        title: str,
        note: str | None,
        tasks: list[CreateOrderTaskInput],
        parts: list[CreateOrderPartInput],
    ) -> int:
        if not title.strip():
            raise ValidationError("Order title cannot be empty.")
        if customer_id is None and not (customer_full_name and customer_full_name.strip()):
            raise ValidationError("Either customer_id or customer_full_name must be provided.")
        if asset_id is None and not (asset_type and asset_label):
            raise ValidationError("Either asset_id or asset_type+asset_label must be provided.")

        if customer_id is None:
            customer_id = self.customer_repo.create(
                conn,
                full_name=customer_full_name.strip(),
                email=(customer_email.strip() if customer_email else None),
                phone=(customer_phone.strip() if customer_phone else None),
                is_vip=is_vip,
            )

        if asset_id is None:
            asset_id = self.asset_repo.create(
                conn,
                customer_id=customer_id,
                asset_type=asset_type.strip(),
                label=asset_label.strip(),
                serial_no=(asset_serial_no.strip() if asset_serial_no else None),
            )

        order_id = self.order_repo.create(
            conn,
            customer_id=customer_id,
            asset_id=asset_id,
            title=title.strip(),
            note=note,
        )

        for t in tasks:
            if not t.description.strip():
                raise ValidationError("Task description cannot be empty.")
            if t.hours < 0:
                raise ValidationError("Task hours cannot be negative.")
            if t.hourly_rate < 0:
                raise ValidationError("Hourly rate cannot be negative.")

            self.task_repo.create(
                conn,
                order_id=order_id,
                description=t.description.strip(),
                hours=float(t.hours),
                hourly_rate=float(t.hourly_rate),
            )

        for p in parts:
            if p.quantity <= 0:
                raise ValidationError("Part quantity must be > 0.")

            part = self.part_repo.get_by_sku(conn, p.sku.strip())
            if part is None:
                raise ValidationError(f"Unknown part SKU: {p.sku}")

            self.order_part_repo.add_part(
                conn,
                order_id=order_id,
                part_id=int(part["id"]),
                quantity=int(p.quantity),
                unit_price=float(part["unit_price"]),
            )

        return order_id

    def complete_order_and_pay(
        self,
        conn: Connection,
        *,
        order_id: int,
        payment_amount: float,
        payment_method: str,
        decrease_stock: bool = True,
    ) -> int:
        if payment_amount < 0:
            raise ValidationError("Payment amount cannot be negative.")
        if not payment_method.strip():
            raise ValidationError("Payment method cannot be empty.")

        self.order_repo.complete(conn, order_id=order_id)

        if decrease_stock:
            lines = self.order_part_repo.list_for_order(conn, order_id)
            for ln in lines:
                self.part_repo.decrease_stock(
                    conn,
                    part_id=int(ln["part_id"]),
                    qty=int(ln["quantity"]),
                )

        payment_id = self.payment_repo.create(
            conn,
            order_id=order_id,
            amount=float(payment_amount),
            method=payment_method.strip(),
            is_refund=False,
        )
        return payment_id