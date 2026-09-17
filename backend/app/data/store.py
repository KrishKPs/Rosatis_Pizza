"""
store.py — the live, editable view of the seeded dataset.

The seed (app/data/seed.py) is generated once and cached here. On top of it we
keep a small OVERRIDES dict for every number CLAUDE.md marks editable: menu
price, menu food cost, ingredient unit cost, channel commission, and each
deal's two modeled behavioral assumptions (incremental_fraction, attach_effect).

Overrides persist to Postgres when DATABASE_URL/POSTGRES_URL is set (hosted),
otherwise to a local JSON file (backend/data_overrides.json), so edits survive
a restart either way. Nothing else needs its own copy of these numbers —
every module reads through the getters below, so an edit re-flows everywhere
at once (CLAUDE.md §8/§12: one source of truth, no duplicated logic).
"""

from __future__ import annotations
import json
import os
import threading
from pathlib import Path

from . import seed as seed_mod

_LOCK = threading.Lock()
_OVERRIDES_PATH = Path(__file__).resolve().parent.parent.parent / "data_overrides.json"

# On Vercel the filesystem is read-only and every request may be a different
# process, so overrides live in Postgres there. Locally there is no DATABASE_URL
# and we keep using the JSON file — no database needed to run this on a laptop.
_DB_URL = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")

_DATASET = None  # lazy singleton, built once from the fixed seed
_OVERRIDES = {
    "menu_price": {},
    "menu_food_cost": {},
    "ingredient_unit_cost": {},
    "channel_commission": {},
    "deal": {},  # deal_id -> {"incremental_fraction": x, "attach_effect": y}
}


def _dataset():
    global _DATASET
    if _DATASET is None:
        _DATASET = seed_mod.generate_dataset()
    return _DATASET


# ---------------------------------------------------------------------------
# Persistence. Two backends behind one pair of functions: Postgres when a
# connection string is present, otherwise the local JSON file. Everything above
# this line is backend-agnostic.
# ---------------------------------------------------------------------------
_DDL = "CREATE TABLE IF NOT EXISTS overrides (id int PRIMARY KEY, data jsonb NOT NULL)"


def _db_load() -> dict | None:
    import psycopg
    with psycopg.connect(_DB_URL) as conn:
        conn.execute(_DDL)
        row = conn.execute("SELECT data FROM overrides WHERE id = 1").fetchone()
    return row[0] if row else None


def _db_save(blob: dict):
    import psycopg
    with psycopg.connect(_DB_URL) as conn:
        conn.execute(_DDL)
        conn.execute(
            "INSERT INTO overrides (id, data) VALUES (1, %s::jsonb) "
            "ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data",
            (json.dumps(blob),),
        )


def _file_load() -> dict | None:
    if not _OVERRIDES_PATH.exists():
        return None
    try:
        with open(_OVERRIDES_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None  # fall back to defaults rather than crash on a bad file


def _file_save(blob: dict):
    """Write-then-rename so a crash mid-write can't truncate the file and lose
    every edited cost — os.replace is atomic on the same filesystem."""
    tmp = _OVERRIDES_PATH.with_name(_OVERRIDES_PATH.name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(blob, f, indent=2)
    os.replace(tmp, _OVERRIDES_PATH)


def load_overrides():
    """Re-read persisted overrides into memory. Called at import and, on
    serverless, once per API request — each invocation gets its own memory, so
    a cost edited by one request is only visible to the next if we re-read."""
    global _OVERRIDES
    saved = _db_load() if _DB_URL else _file_load()
    if not saved:
        return
    for k in _OVERRIDES:
        if k in saved:
            _OVERRIDES[k] = saved[k]


def _save_overrides():
    (_db_save if _DB_URL else _file_save)(_OVERRIDES)


def using_database() -> bool:
    return bool(_DB_URL)


load_overrides()

# ---------------------------------------------------------------------------
# Raw (non-editable identity/shape) accessors
# ---------------------------------------------------------------------------
def menu() -> list:
    return _dataset()["menu"]


def menu_by_id() -> dict:
    return _dataset()["menu_by_id"]


def ingredients() -> dict:
    return _dataset()["ingredients"]


def channels() -> dict:
    return _dataset()["channels"]


def deals() -> dict:
    return _dataset()["deals"]


def customers() -> list:
    return _dataset()["customers"]


def orders() -> list:
    return _dataset()["orders"]


def categories() -> list:
    return seed_mod.CATEGORIES


def start_date():
    return seed_mod.START


def num_days() -> int:
    return seed_mod.DAYS


# ---------------------------------------------------------------------------
# Editable getters — every module must read cost/commission/deal-assumption
# numbers through these, never off the raw dataclasses above.
# ---------------------------------------------------------------------------
def ingredient_unit_cost(ingredient_id: str) -> float:
    ov = _OVERRIDES["ingredient_unit_cost"].get(ingredient_id)
    return ov if ov is not None else ingredients()[ingredient_id].unit_cost


def menu_price(item_id: str) -> float:
    ov = _OVERRIDES["menu_price"].get(item_id)
    return ov if ov is not None else menu_by_id()[item_id].price


def menu_food_cost(item_id: str) -> float:
    """Derived from the recipe + current (possibly edited) ingredient costs,
    unless the owner has directly overridden this item's food cost."""
    ov = _OVERRIDES["menu_food_cost"].get(item_id)
    if ov is not None:
        return ov
    item = menu_by_id()[item_id]
    return round(sum(ingredient_unit_cost(iid) * qty for iid, qty in item.recipe.items()), 2)


def is_food_cost_overridden(item_id: str) -> bool:
    return item_id in _OVERRIDES["menu_food_cost"]


def channel_commission(channel_id: str) -> float:
    ov = _OVERRIDES["channel_commission"].get(channel_id)
    return ov if ov is not None else channels()[channel_id].commission


def deal_incremental_fraction(deal_id: str) -> float:
    ov = _OVERRIDES["deal"].get(deal_id, {}).get("incremental_fraction")
    return ov if ov is not None else deals()[deal_id].incremental_fraction


def deal_attach_effect(deal_id: str) -> float:
    ov = _OVERRIDES["deal"].get(deal_id, {}).get("attach_effect")
    return ov if ov is not None else deals()[deal_id].attach_effect


# ---------------------------------------------------------------------------
# Setters — validate lightly, persist immediately.
# ---------------------------------------------------------------------------
def set_menu_price(item_id: str, value: float):
    if item_id not in menu_by_id():
        raise KeyError(item_id)
    with _LOCK:
        _OVERRIDES["menu_price"][item_id] = round(float(value), 2)
        _save_overrides()


def set_menu_food_cost(item_id: str, value: float | None):
    """value=None clears the override and reverts to recipe-derived cost."""
    if item_id not in menu_by_id():
        raise KeyError(item_id)
    with _LOCK:
        if value is None:
            _OVERRIDES["menu_food_cost"].pop(item_id, None)
        else:
            _OVERRIDES["menu_food_cost"][item_id] = round(float(value), 2)
        _save_overrides()


def set_ingredient_unit_cost(ingredient_id: str, value: float):
    if ingredient_id not in ingredients():
        raise KeyError(ingredient_id)
    with _LOCK:
        _OVERRIDES["ingredient_unit_cost"][ingredient_id] = round(float(value), 4)
        _save_overrides()


def set_channel_commission(channel_id: str, value: float):
    if channel_id not in channels():
        raise KeyError(channel_id)
    with _LOCK:
        _OVERRIDES["channel_commission"][channel_id] = round(float(value), 4)
        _save_overrides()


def set_deal_assumptions(deal_id: str, incremental_fraction: float | None = None,
                          attach_effect: float | None = None):
    if deal_id not in deals():
        raise KeyError(deal_id)
    with _LOCK:
        cur = _OVERRIDES["deal"].setdefault(deal_id, {})
        if incremental_fraction is not None:
            cur["incremental_fraction"] = round(float(incremental_fraction), 3)
        if attach_effect is not None:
            cur["attach_effect"] = round(float(attach_effect), 3)
        _save_overrides()


def reset_overrides():
    """Drop every override and revert to seeded defaults."""
    global _OVERRIDES
    with _LOCK:
        _OVERRIDES = {
            "menu_price": {}, "menu_food_cost": {},
            "ingredient_unit_cost": {}, "channel_commission": {}, "deal": {},
        }
        _save_overrides()
