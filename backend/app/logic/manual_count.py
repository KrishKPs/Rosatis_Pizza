"""
manual_count.py — the digital version of the clipboard inventory check.

The worker still walks the store and counts everything by hand (pizza boxes by
size, dough, napkins, gloves, ...) — this module just gives that count a home
in the app instead of a piece of paper, and turns it straight into "what to
order next".

For recipe-tracked items (food/packaging) we also show the order-derived
"system expected" number next to the hand count, so a big gap is a signal
worth noticing (over-portioning, waste, a miscount, theft) — but the hand
count is always what drives status and reorder suggestions, because that's
what's actually on the shelf right now. Supply items (napkins, bags, gloves,
...) have no recipe at all, so the hand count is the *only* number that exists
for them until someone counts them.
"""

from __future__ import annotations

from app.data import store, counts as counts_store
from . import inventory as inv_logic


def _system_expected() -> dict[str, float]:
    stock = inv_logic.simulate_stock_levels()
    return {iid: round(v, 1) for iid, v in stock.items()}


def count_sheet() -> dict:
    system = _system_expected()
    latest = counts_store.latest_counts()
    rows = []
    for iid, ing in store.ingredients().items():
        last = latest.get(iid)
        expected = system.get(iid) if ing.kind != "supply" else None
        on_hand = last["qty"] if last else expected
        variance = round(last["qty"] - expected, 1) if (last and expected is not None) else None

        if on_hand is None:
            status = "uncounted"
        elif on_hand <= 0:
            status = "out"
        elif on_hand <= ing.reorder_point:
            status = "low"
        else:
            status = "ok"

        suggested_order_qty = round(max(ing.restock_to - on_hand, 0), 1) if on_hand is not None else None

        rows.append({
            "ingredient_id": iid,
            "name": ing.name,
            "unit": ing.unit,
            "kind": ing.kind,
            "unit_cost": store.ingredient_unit_cost(iid),
            "reorder_point": ing.reorder_point,
            "restock_to": ing.restock_to,
            "system_expected": expected,
            "last_count_qty": last["qty"] if last else None,
            "last_counted_at": last["counted_at"] if last else None,
            "last_counted_by": last["counted_by"] if last else None,
            "on_hand": on_hand,
            "variance": variance,
            "status": status,
            "suggested_order_qty": suggested_order_qty,
        })

    order = {"packaging": 0, "food": 1, "supply": 2}
    status_rank = {"out": 0, "low": 1, "uncounted": 2, "ok": 3}
    rows.sort(key=lambda r: (order.get(r["kind"], 9), status_rank.get(r["status"], 9), r["name"]))
    return rows


def count_kpis(rows: list[dict] | None = None) -> dict:
    rows = rows if rows is not None else count_sheet()
    sess = counts_store.sessions(limit=1)
    return {
        "items_to_reorder": len([r for r in rows if r["status"] in ("low", "out")]),
        "items_out": len([r for r in rows if r["status"] == "out"]),
        "items_never_counted": len([r for r in rows if r["last_count_qty"] is None]),
        "last_session_at": sess[0]["counted_at"] if sess else None,
        "last_session_by": sess[0]["counted_by"] if sess else None,
    }


def reorder_list(rows: list[dict] | None = None) -> list[dict]:
    rows = rows if rows is not None else count_sheet()
    flagged = [r for r in rows if r["status"] in ("low", "out")]
    return [{
        "ingredient_id": r["ingredient_id"],
        "name": r["name"],
        "unit": r["unit"],
        "kind": r["kind"],
        "on_hand": r["on_hand"],
        "reorder_point": r["reorder_point"],
        "suggested_order_qty": r["suggested_order_qty"],
        "status": r["status"],
    } for r in flagged]


def record_count(counted_by: str, entries: list[dict], note: str | None = None) -> dict:
    known = store.ingredients()
    clean: dict[str, float] = {}
    for e in entries:
        iid = e["ingredient_id"]
        if iid not in known:
            raise KeyError(iid)
        clean[iid] = round(float(e["counted_qty"]), 1)
    counts_store.record_session(counted_by.strip(), clean, note)
    rows = count_sheet()
    return {
        "kpis": count_kpis(rows),
        "items": rows,
        "reorder_list": reorder_list(rows),
    }


def history(limit: int = 20) -> list[dict]:
    out = []
    for s in counts_store.sessions(limit):
        out.append({
            "id": s["id"],
            "counted_at": s["counted_at"],
            "counted_by": s["counted_by"],
            "note": s.get("note"),
            "items_counted": len(s["entries"]),
        })
    return out
