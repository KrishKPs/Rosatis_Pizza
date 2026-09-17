"""Global lookups the frontend needs for filter controls, plus a reset
endpoint so the owner can undo every edited cost/assumption at once."""

from __future__ import annotations
from fastapi import APIRouter

from app.data import store

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("")
def meta():
    orders = store.orders()
    return {
        "date_min": min(o.ts for o in orders).date().isoformat(),
        "date_max": max(o.ts for o in orders).date().isoformat(),
        "channels": [{"id": c.id, "name": c.name, "commission": store.channel_commission(c.id)}
                     for c in store.channels().values()],
        "categories": store.categories(),
        "store_name": "Rosati's Pizza — Raleigh",
        "store_address": "6615 Falls of Neuse Rd, Suite 101, Raleigh, NC 27615",
    }


@router.post("/reset")
def reset():
    store.reset_overrides()
    return {"status": "reset"}
