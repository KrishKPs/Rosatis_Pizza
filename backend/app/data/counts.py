"""
counts.py — persisted manual inventory counts.

Tony's worker still walks the store with a clipboard and counts what's actually
on the shelf (boxes by size, napkins, gloves, dough, everything) — this file is
that clipboard, digitized. Nothing here is generated or simulated: every value
comes from a person typing in a number they physically counted.

Persists to backend/inventory_counts.json — same append-only-history + latest-
snapshot shape as data_overrides.json, kept in its own file because it's a log
of physical events (who counted what, when), not an editable default.
"""

from __future__ import annotations
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.Lock()
_PATH = Path(__file__).resolve().parent.parent.parent / "inventory_counts.json"

# {"sessions": [{"id", "counted_at", "counted_by", "note", "entries": {ingredient_id: qty}}],
#  "latest": {ingredient_id: {"qty", "counted_at", "counted_by", "session_id"}}}
_STATE = {"sessions": [], "latest": {}}


def _load():
    global _STATE
    if _PATH.exists():
        try:
            with open(_PATH) as f:
                saved = json.load(f)
            if "sessions" in saved and "latest" in saved:
                _STATE = saved
        except (json.JSONDecodeError, OSError):
            pass  # fall back to empty history rather than crash the app


def _save():
    with open(_PATH, "w") as f:
        json.dump(_STATE, f, indent=2)


_load()


def latest_counts() -> dict:
    """ingredient_id -> {"qty", "counted_at", "counted_by", "session_id"}"""
    return _STATE["latest"]


def sessions(limit: int = 20) -> list[dict]:
    return list(reversed(_STATE["sessions"]))[:limit]


def record_session(counted_by: str, entries: dict[str, float], note: str | None = None) -> dict:
    """entries: ingredient_id -> counted_qty. Appends a session to history and
    updates the latest-known count for every ingredient it touched."""
    with _LOCK:
        session_id = f"cnt_{len(_STATE['sessions']) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()
        session = {
            "id": session_id,
            "counted_at": now,
            "counted_by": counted_by,
            "note": note,
            "entries": entries,
        }
        _STATE["sessions"].append(session)
        for iid, qty in entries.items():
            _STATE["latest"][iid] = {
                "qty": qty, "counted_at": now, "counted_by": counted_by, "session_id": session_id,
            }
        _save()
        return session
