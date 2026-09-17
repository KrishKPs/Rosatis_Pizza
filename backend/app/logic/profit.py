"""
profit.py — the profit math, in ONE place (CLAUDE.md §8: "Never recompute
these differently in the UI. One source of truth.").

Every module (Sales, Deal Optimizer, Inventory, Menu, Orders, Customers) calls
into this file rather than reimplementing item margin, order net profit, deal
true profit, or channel profit. All functions read current (possibly edited)
costs through app.data.store, so an edited cost re-flows every number that
depends on it, everywhere, immediately.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import date

from app.data import store

# Categories that count as "add-ons" pulled into an order (CLAUDE.md glossary:
# attach = "extra items pulled into an order (drinks/wings/sides)"). Pizza,
# Pasta, Sandwiches, and Calzone are the "meal" the customer came for.
ATTACH_CATEGORIES = {"Wings", "Appetizers", "Salad", "Beverages", "Desserts"}


# ---------------------------------------------------------------------------
# Item-level
# ---------------------------------------------------------------------------
def item_margin(item_id: str) -> float:
    return round(store.menu_price(item_id) - store.menu_food_cost(item_id), 2)


def item_margin_pct(item_id: str) -> float:
    price = store.menu_price(item_id)
    return round(100 * item_margin(item_id) / price, 1) if price else 0.0


def _avg_attach_margin() -> float:
    items = [m for m in store.menu() if m.category in ATTACH_CATEGORIES]
    if not items:
        return 0.0
    return sum(item_margin(m.id) for m in items) / len(items)


# ---------------------------------------------------------------------------
# Order-level
# ---------------------------------------------------------------------------
def order_food_cost(order) -> float:
    menu_by_id = store.menu_by_id()
    return round(sum(store.menu_food_cost(l.item_id) * l.qty for l in order.lines
                      if l.item_id in menu_by_id), 2)


def order_commission(order) -> float:
    return round(order.revenue * store.channel_commission(order.channel), 2)


def order_net_profit(order) -> float:
    return round(order.revenue - order_food_cost(order) - order_commission(order), 2)


def order_full_price_subtotal(order) -> float:
    """What this basket would cost today at menu price, no deal applied —
    used to show the discount actually given."""
    menu_by_id = store.menu_by_id()
    return round(sum(store.menu_price(l.item_id) * l.qty for l in order.lines
                      if l.item_id in menu_by_id), 2)


def order_attach_revenue(order) -> float:
    menu_by_id = store.menu_by_id()
    return round(sum(store.menu_price(l.item_id) * l.qty for l in order.lines
                      if l.item_id in menu_by_id and menu_by_id[l.item_id].category in ATTACH_CATEGORIES), 2)


# ---------------------------------------------------------------------------
# Filtering helper — every module slices the same order list by date range
# ---------------------------------------------------------------------------
def filter_orders(orders=None, start: date | None = None, end: date | None = None,
                   channel: str | None = None):
    orders = store.orders() if orders is None else orders
    out = orders
    if start is not None:
        out = [o for o in out if o.ts.date() >= start]
    if end is not None:
        out = [o for o in out if o.ts.date() <= end]
    if channel is not None:
        out = [o for o in out if o.channel == channel]
    return out


# ---------------------------------------------------------------------------
# Sales & Analytics
# ---------------------------------------------------------------------------
def sales_summary(orders_subset) -> dict:
    n = len(orders_subset)
    revenue = round(sum(o.revenue for o in orders_subset), 2)
    net = round(sum(order_net_profit(o) for o in orders_subset), 2)
    return {
        "revenue": revenue,
        "order_count": n,
        "net_profit": net,
        "net_margin_pct": round(100 * net / revenue, 1) if revenue else 0.0,
        "avg_order_value": round(revenue / n, 2) if n else 0.0,
    }


def revenue_profit_over_time(orders_subset) -> list[dict]:
    by_day = defaultdict(lambda: {"revenue": 0.0, "net_profit": 0.0, "order_count": 0})
    for o in orders_subset:
        d = by_day[o.ts.date().isoformat()]
        d["revenue"] += o.revenue
        d["net_profit"] += order_net_profit(o)
        d["order_count"] += 1
    return [{"date": d, **{k: round(v, 2) if k != "order_count" else v for k, v in vals.items()}}
            for d, vals in sorted(by_day.items())]


def sales_by_category(orders_subset) -> list[dict]:
    menu_by_id = store.menu_by_id()
    rev = defaultdict(float)
    profit = defaultdict(float)
    for o in orders_subset:
        for l in o.lines:
            item = menu_by_id.get(l.item_id)
            if not item:
                continue
            line_rev = store.menu_price(l.item_id) * l.qty
            line_cost = store.menu_food_cost(l.item_id) * l.qty
            rev[item.category] += line_rev
            profit[item.category] += (line_rev - line_cost)
    return [{"category": c, "revenue": round(rev[c], 2), "profit": round(profit[c], 2)}
            for c in sorted(rev, key=lambda c: -rev[c])]


def channel_profit_summary(orders_subset) -> list[dict]:
    rev = defaultdict(float)
    net = defaultdict(float)
    cnt = defaultdict(int)
    for o in orders_subset:
        rev[o.channel] += o.revenue
        net[o.channel] += order_net_profit(o)
        cnt[o.channel] += 1
    out = []
    for cid, ch in store.channels().items():
        r = round(rev[cid], 2)
        out.append({
            "channel_id": cid,
            "channel_name": ch.name,
            "commission_pct": round(store.channel_commission(cid) * 100, 1),
            "revenue": r,
            "net_profit": round(net[cid], 2),
            "net_margin_pct": round(100 * net[cid] / r, 1) if r else 0.0,
            "order_count": cnt[cid],
        })
    return sorted(out, key=lambda x: -x["revenue"])


def day_hour_heat(orders_subset) -> list[dict]:
    grid = defaultdict(lambda: {"orders": 0, "revenue": 0.0})
    for o in orders_subset:
        key = (o.ts.weekday(), o.ts.hour)
        grid[key]["orders"] += 1
        grid[key]["revenue"] += o.revenue
    return [{"weekday": wd, "hour": hr, "orders": v["orders"], "revenue": round(v["revenue"], 2)}
            for (wd, hr), v in sorted(grid.items())]


def top_items(orders_subset, n: int = 10) -> list[dict]:
    menu_by_id = store.menu_by_id()
    qty = defaultdict(int)
    rev = defaultdict(float)
    for o in orders_subset:
        for l in o.lines:
            if l.item_id in menu_by_id:
                qty[l.item_id] += l.qty
                rev[l.item_id] += store.menu_price(l.item_id) * l.qty
    ranked = sorted(qty.items(), key=lambda kv: -kv[1])[:n]
    return [{"item_id": iid, "name": menu_by_id[iid].name, "category": menu_by_id[iid].category,
             "qty_sold": q, "revenue": round(rev[iid], 2)} for iid, q in ranked]


# ---------------------------------------------------------------------------
# Deal Profit Optimizer — the differentiator (CLAUDE.md §7.2)
# ---------------------------------------------------------------------------
def deal_true_profit_stats(deal_id: str, orders_subset, incremental_fraction: float | None = None,
                            attach_effect: float | None = None) -> dict:
    """True incremental profit = actual profit earned by deal orders, minus
    the margin given away to customers who'd have ordered anyway (the
    non-incremental share, valued at what a normal full-price order nets),
    plus a modeled bonus for the extra add-ons the deal tends to pull in.

    Pass incremental_fraction/attach_effect to preview hypothetical
    assumptions (the Deal Optimizer's what-if control) without persisting
    them; omit both to use the current saved (possibly edited) values."""
    deal = store.deals()[deal_id]
    deal_orders = [o for o in orders_subset if o.deal_id == deal_id]
    n = len(deal_orders)

    non_deal_orders = [o for o in orders_subset if o.deal_id is None]
    baseline_profit_per_order = (
        sum(order_net_profit(o) for o in non_deal_orders) / len(non_deal_orders)
        if non_deal_orders else 0.0
    )

    revenue = round(sum(o.revenue for o in deal_orders), 2)
    discount_given = round(sum(order_full_price_subtotal(o) - o.revenue for o in deal_orders), 2)
    food_cost = round(sum(order_food_cost(o) for o in deal_orders), 2)
    commission = round(sum(order_commission(o) for o in deal_orders), 2)
    attach_revenue = round(sum(order_attach_revenue(o) for o in deal_orders), 2)
    actual_profit = round(sum(order_net_profit(o) for o in deal_orders), 2)

    if incremental_fraction is None:
        incremental_fraction = store.deal_incremental_fraction(deal_id)
    if attach_effect is None:
        attach_effect = store.deal_attach_effect(deal_id)

    margin_given_away = round((1 - incremental_fraction) * n * baseline_profit_per_order, 2)
    attach_bonus = round(attach_effect * n * _avg_attach_margin(), 2)
    true_profit = round(actual_profit - margin_given_away + attach_bonus, 2)

    return {
        "deal_id": deal_id,
        "name": deal.name,
        "code": deal.code,
        "type": deal.type,
        "availability": deal.availability,
        "redemptions": n,
        "revenue": revenue,
        "discount_given": discount_given,
        "food_cost": food_cost,
        "commission": commission,
        "attach_revenue": attach_revenue,
        "actual_profit": actual_profit,
        "incremental_fraction": incremental_fraction,
        "attach_effect": attach_effect,
        "baseline_profit_per_order": round(baseline_profit_per_order, 2),
        "margin_given_away": margin_given_away,
        "attach_bonus": attach_bonus,
        "true_profit": true_profit,
        "true_profit_per_redemption": round(true_profit / n, 2) if n else 0.0,
        "verdict": _deal_verdict(deal, n, true_profit, incremental_fraction, attach_effect),
    }


def _deal_verdict(deal, n, true_profit, incremental_fraction, attach_effect) -> str:
    if n == 0:
        return f"{deal.name} hasn't been used in this period yet."
    if true_profit <= 0:
        return (f"{deal.name} is losing money — too much of it goes to customers "
                f"who'd have ordered anyway. Needs more new customers or bigger add-on sales "
                f"to pay for itself.")
    if incremental_fraction < 0.4 and attach_effect < 0.35:
        return (f"{deal.name} is barely breaking even. It only really pays off when it "
                f"pulls in add-ons (drinks, wings) or a genuinely new customer.")
    return f"{deal.name} is one of your better earners — a healthy share of these are new business or come with extra add-ons."


def rank_deals(orders_subset) -> list[dict]:
    stats = [deal_true_profit_stats(did, orders_subset) for did in store.deals()]
    return sorted(stats, key=lambda s: -s["true_profit"])


# ---------------------------------------------------------------------------
# Customers & Loyalty
# ---------------------------------------------------------------------------
def customer_summary(orders_subset) -> dict:
    active_ids = {o.customer_id for o in orders_subset}
    custs = [c for c in store.customers() if c.id in active_ids]
    total = len(custs)
    repeat = len([c for c in custs if c.is_repeat])
    return {
        "total_customers": total,
        "repeat_customers": repeat,
        "repeat_rate_pct": round(100 * repeat / total, 1) if total else 0.0,
        "avg_visits": round(sum(c.order_count for c in custs) / total, 1) if total else 0.0,
        "loyalty_points_outstanding": sum(c.loyalty_points for c in custs),
    }
