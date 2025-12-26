from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

OrderStatus = Literal["new", "in_progress", "done", "cancelled"]


@dataclass(frozen=True)
class Customer:
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    is_vip: bool
    created_at: datetime


@dataclass(frozen=True)
class Asset:
    id: int
    customer_id: int
    asset_type: str
    label: str
    serial_no: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class Part:
    id: int
    sku: str
    name: str
    unit_price: Decimal
    stock_qty: int
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class ServiceOrder:
    id: int
    customer_id: int
    asset_id: int
    status: OrderStatus
    title: str
    note: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


@dataclass(frozen=True)
class ServiceTask:
    id: int
    order_id: int
    description: str
    hours: Decimal
    hourly_rate: Decimal


@dataclass(frozen=True)
class Payment:
    id: int
    order_id: int
    amount: Decimal
    paid_at: datetime
    method: str
    is_refund: bool