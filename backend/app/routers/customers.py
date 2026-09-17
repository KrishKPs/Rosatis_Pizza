"""Customers & Loyalty — CLAUDE.md §7.6."""

from __future__ import annotations
from fastapi import APIRouter, Depends

from app.data import store
from app.logic import profit
from .common import date_range_params, get_filtered_orders

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/summary")
def summary(params: dict = Depends(date_range_params)):
    return profit.customer_summary(get_filtered_orders(params))


@router.get("/top")
def top_customers(n: int = 10, by: str = "total_spent"):
    key = by if by in ("total_spent", "order_count", "loyalty_points") else "total_spent"
    ranked = sorted(store.customers(), key=lambda c: -getattr(c, key))[:n]
    return [{
        "customer_id": c.id, "name": c.name,
        "first_order_date": c.first_order_date.isoformat(),
        "order_count": c.order_count, "total_spent": c.total_spent,
        "loyalty_points": c.loyalty_points, "is_repeat": c.is_repeat,
    } for c in ranked]


@router.get("")
def list_customers():
    return [{
        "customer_id": c.id, "name": c.name,
        "first_order_date": c.first_order_date.isoformat(),
        "order_count": c.order_count, "total_spent": c.total_spent,
        "loyalty_points": c.loyalty_points, "is_repeat": c.is_repeat,
    } for c in sorted(store.customers(), key=lambda c: -c.total_spent)]
