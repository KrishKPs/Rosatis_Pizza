"""
inventory.py — inventory depletion + alerts.

Ingredients deplete as the seeded orders come in, via the same recipe map
that drives menu food cost (app/data/store.menu_food_cost). There is no
second decorative dataset: the burn-down and low-stock alerts are computed
straight from app.data.store.orders().
"""

from __future__ import annotations
from collections import defaultdict

from app.data import store


def simulate_stock_levels(orders_subset=None, restock_every_days: int = 14) -> dict[str, float]:
    """Replay depletion + periodic restock across the given orders (default:
    the full seeded history) and return each ingredient's final stock level."""
    orders_subset = store.orders() if orders_subset is None else orders_subset
    ingredients = store.ingredients()
    stock = {iid: ing.restock_to for iid, ing in ingredients.items()}
    if not orders_subset:
        return stock

    menu_by_id = store.menu_by_id()
    last_restock = orders_subset[0].ts.date()
    for o in orders_subset:
        if (o.ts.date() - last_restock).days >= restock_every_days:
            stock = {iid: ing.restock_to for iid, ing in ingredients.items()}
            last_restock = o.ts.date()
        for l in o.lines:
            item = menu_by_id.get(l.item_id)
            if not item:
                continue
            for iid, qty in item.recipe.items():
                stock[iid] -= qty * l.qty
    return stock


def inventory_table(orders_subset=None) -> list[dict]:
    """Recipe-tracked stock only (food + packaging) — this is the computed,
    order-derived view. Supply items (napkins, gloves, ...)
    never appear in a recipe, so there's nothing here to compute for them; they
    live in the manual count sheet instead (app/logic/manual_count.py)."""
    stock = simulate_stock_levels(orders_subset)
    out = []
    for iid, ing in store.ingredients().items():
        if ing.kind == "supply":
            continue
        level = round(stock[iid], 1)
        unit_cost = store.ingredient_unit_cost(iid)
        status = "out" if level <= 0 else ("low" if level <= ing.reorder_point else "ok")
        out.append({
            "ingredient_id": iid,
            "name": ing.name,
            "unit": ing.unit,
            "kind": ing.kind,
            "stock_level": level,
            "unit_cost": unit_cost,
            "reorder_point": ing.reorder_point,
            "restock_to": ing.restock_to,
            "value": round(level * unit_cost, 2),
            "status": status,
            "low_stock": status != "ok",
        })
    return sorted(out, key=lambda r: (r["status"] != "out", r["status"] != "low", r["name"]))


def inventory_kpis(orders_subset=None) -> dict:
    table = inventory_table(orders_subset)
    return {
        "items_low_or_out": len([r for r in table if r["low_stock"]]),
        "items_out": len([r for r in table if r["status"] == "out"]),
        "total_inventory_value": round(sum(max(r["value"], 0) for r in table), 2),
    }


def usage_last_n_days(orders_subset, n_days: int = 14) -> list[dict]:
    """Ingredient burn-down: total quantity consumed per day for the last
    n_days of the given order set — lets the owner see what recent orders
    actually consumed."""
    if not orders_subset:
        return []
    menu_by_id = store.menu_by_id()
    end = max(o.ts.date() for o in orders_subset)
    start = end - __import__("datetime").timedelta(days=n_days - 1)
    usage = defaultdict(lambda: defaultdict(float))  # date -> ingredient_id -> qty
    for o in orders_subset:
        d = o.ts.date()
        if d < start or d > end:
            continue
        for l in o.lines:
            item = menu_by_id.get(l.item_id)
            if not item:
                continue
            for iid, qty in item.recipe.items():
                usage[d.isoformat()][iid] += qty * l.qty
    return [{"date": d, "usage": {iid: round(q, 1) for iid, q in ingredient_qtys.items()}}
            for d, ingredient_qtys in sorted(usage.items())]
