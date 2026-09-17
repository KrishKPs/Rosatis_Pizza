"""Inventory & Ingredients."""

from __future__ import annotations
from fastapi import APIRouter, HTTPException

from app.data import store
from app.logic import inventory as inv_logic
from app.logic import manual_count
from app.models.schemas import CountSubmission, IngredientUpdate

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
def get_inventory():
    return {
        "kpis": inv_logic.inventory_kpis(),
        "items": inv_logic.inventory_table(),
    }


@router.get("/usage")
def get_usage(days: int = 14):
    return inv_logic.usage_last_n_days(store.orders(), n_days=days)


@router.patch("/{ingredient_id}")
def update_ingredient(ingredient_id: str, body: IngredientUpdate):
    if ingredient_id not in store.ingredients():
        raise HTTPException(404, "ingredient not found")
    store.set_ingredient_unit_cost(ingredient_id, body.unit_cost)
    table = inv_logic.inventory_table()
    return next(r for r in table if r["ingredient_id"] == ingredient_id)


# ---------------------------------------------------------------------------
# Manual count sheet — the digitized clipboard walk-through. Still a manual
# count (a person types in what they physically counted); the app just turns
# it straight into status + a reorder list instead of staying on paper.
# ---------------------------------------------------------------------------
@router.get("/count-sheet")
def get_count_sheet():
    rows = manual_count.count_sheet()
    return {
        "kpis": manual_count.count_kpis(rows),
        "items": rows,
        "reorder_list": manual_count.reorder_list(rows),
    }


@router.post("/count")
def submit_count(body: CountSubmission):
    try:
        return manual_count.record_count(
            body.counted_by, [e.model_dump() for e in body.entries], body.note,
        )
    except KeyError as e:
        raise HTTPException(404, f"unknown ingredient: {e.args[0]}")


@router.get("/count-history")
def get_count_history(limit: int = 20):
    return manual_count.history(limit)
