"""Orders & Channels — CLAUDE.md §7.5, the live-feeling order feed."""

from __future__ import annotations
from fastapi import APIRouter, Depends

from app.data import store
from app.logic import profit
from .common import date_range_params, get_filtered_orders

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _serialize(o) -> dict:
    menu_by_id = store.menu_by_id()
    customer = next((c for c in store.customers() if c.id == o.customer_id), None)
    return {
        "order_id": o.id,
        "timestamp": o.ts.isoformat(),
        "channel": o.channel,
        "channel_name": store.channels()[o.channel].name,
        "customer_name": customer.name if customer else "Guest",
        "items": [{"item_id": l.item_id, "name": menu_by_id[l.item_id].name, "qty": l.qty}
                  for l in o.lines if l.item_id in menu_by_id],
        "deal_id": o.deal_id,
        "deal_name": store.deals()[o.deal_id].name if o.deal_id else None,
        "revenue": o.revenue,
        "food_cost": profit.order_food_cost(o),
        "commission_paid": profit.order_commission(o),
        "net_profit": profit.order_net_profit(o),
    }


@router.get("")
def list_orders(limit: int = 50, params: dict = Depends(date_range_params)):
    orders_subset = get_filtered_orders(params)
    orders_subset = sorted(orders_subset, key=lambda o: o.ts, reverse=True)[:limit]
    return [_serialize(o) for o in orders_subset]


@router.get("/channels")
def channels_breakdown(params: dict = Depends(date_range_params)):
    return profit.channel_profit_summary(get_filtered_orders(params))
