"""Checks for the override persistence layer (app/data/store.py).

Run: backend/.venv/bin/python test_store.py

Covers the money path — the owner's edited costs. Both backends: the local JSON
file, and the Postgres branch used when DATABASE_URL/POSTGRES_URL is set. The
Postgres SQL is checked against a fake connection, so this needs no database.
"""
import json
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.data import store  # noqa: E402

# Work on a throwaway file so running the tests never touches real edits.
store._OVERRIDES_PATH = Path(tempfile.mkdtemp()) / "data_overrides.json"
store._OVERRIDES = {k: {} for k in store._OVERRIDES}

item = store.menu()[0].id
recipe_cost = store.menu_food_cost(item)

# --- file backend ---------------------------------------------------------
assert not store.using_database(), "no DATABASE_URL -> file backend"
store.set_menu_food_cost(item, 9.99)
assert store.menu_food_cost(item) == 9.99
assert json.load(open(store._OVERRIDES_PATH))["menu_food_cost"][item] == 9.99

# an edit survives a restart
store._OVERRIDES = {k: {} for k in store._OVERRIDES}
store.load_overrides()
assert store.menu_food_cost(item) == 9.99, "edit must survive a restart"

# atomic write leaves no temp file behind
assert not list(store._OVERRIDES_PATH.parent.glob("*.tmp")), "temp file left behind"

# a corrupt file degrades to seeded defaults instead of crashing the app
open(store._OVERRIDES_PATH, "w").write("{not json")
store._OVERRIDES = {k: {} for k in store._OVERRIDES}
store.load_overrides()
assert store.menu_food_cost(item) == recipe_cost, "corrupt file -> seeded defaults"

# clearing an override reverts to the recipe-derived cost
store.set_menu_food_cost(item, 5.0)
store.set_menu_food_cost(item, None)
assert store.menu_food_cost(item) == recipe_cost, "None clears the override"


# --- Postgres backend: exercise the real SQL against a fake connection -----
class FakeConn:
    def __init__(self):
        self.sql = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, params=None):
        self.sql.append((" ".join(q.split()), params))
        return self

    def fetchone(self):
        return None


fake = FakeConn()
sys.modules["psycopg"] = types.SimpleNamespace(connect=lambda url: fake)
store._DB_URL = "postgres://fake"
assert store.using_database()

store._db_save({"menu_price": {"x": 1}})
stmts = [q for q, _ in fake.sql]
assert any("CREATE TABLE IF NOT EXISTS overrides" in q for q in stmts), stmts
upsert, params = next((q, p) for q, p in fake.sql if q.startswith("INSERT"))
assert "ON CONFLICT (id) DO UPDATE" in upsert, "second save must update, not fail"
assert "%s::jsonb" in upsert, "blob must be cast to jsonb"
assert json.loads(params[0]) == {"menu_price": {"x": 1}}, "payload must be JSON text"
assert store._db_load() is None, "empty table -> None -> seeded defaults"

print("store persistence: all checks passed")
