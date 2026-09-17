"""Pydantic request bodies for the editable-cost endpoints (costs are visible and editable everywhere, never hidden magic)."""

from __future__ import annotations
from pydantic import BaseModel, Field


class MenuItemUpdate(BaseModel):
    price: float | None = Field(default=None, gt=0)
    food_cost: float | None = Field(default=None, ge=0)
    reset_food_cost: bool = False  # true -> revert to recipe-derived cost


class IngredientUpdate(BaseModel):
    unit_cost: float = Field(gt=0)


class ChannelUpdate(BaseModel):
    commission: float = Field(ge=0, le=1)


class DealAssumptionsUpdate(BaseModel):
    incremental_fraction: float | None = Field(default=None, ge=0, le=1)
    attach_effect: float | None = Field(default=None, ge=0, le=1)


class CountEntry(BaseModel):
    ingredient_id: str
    counted_qty: float = Field(ge=0)


class CountSubmission(BaseModel):
    counted_by: str = Field(min_length=1, max_length=60)
    entries: list[CountEntry] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=280)
