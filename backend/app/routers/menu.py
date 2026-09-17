"""Menu & Pricing — CLAUDE.md §7.4. Editing a food cost re-flows margins and
every downstream profit number (single source of truth, §12)."""

from __future__ import annotations
from fastapi import APIRouter, HTTPException

from app.data import store
from app.logic import profit
from app.models.schemas import MenuItemUpdate

router = APIRouter(prefix="/api/menu", tags=["menu"])


def _serialize(item) -> dict:
    return {
        "item_id": item.id,
        "name": item.name,
        "category": item.category,
        "price": store.menu_price(item.id),
        "price_src": item.price_src,
        "food_cost": store.menu_food_cost(item.id),
        "food_cost_overridden": store.is_food_cost_overridden(item.id),
        "margin": profit.item_margin(item.id),
        "margin_pct": profit.item_margin_pct(item.id),
    }


@router.get("")
def list_menu(category: str | None = None):
    items = store.menu()
    if category:
        items = [m for m in items if m.category == category]
    return sorted((_serialize(m) for m in items), key=lambda r: -r["margin_pct"])


@router.get("/categories")
def list_categories():
    return store.categories()


@router.patch("/{item_id}")
def update_menu_item(item_id: str, body: MenuItemUpdate):
    if item_id not in store.menu_by_id():
        raise HTTPException(404, "menu item not found")
    if body.price is not None:
        store.set_menu_price(item_id, body.price)
    if body.reset_food_cost:
        store.set_menu_food_cost(item_id, None)
    elif body.food_cost is not None:
        store.set_menu_food_cost(item_id, body.food_cost)
    return _serialize(store.menu_by_id()[item_id])
