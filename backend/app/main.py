"""FastAPI app — Rosati's Ops backend.

Simple JSON endpoints over the single seeded data layer (app/data). No logic
duplicated across languages: the profit math lives in app/logic once and
every route calls it (CLAUDE.md §4/§8).
"""

from __future__ import annotations
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data import store
from app.routers import sales, deals, inventory, menu, orders, customers, meta

app = FastAPI(title="Rosati's Ops API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(sales.router)
app.include_router(deals.router)
app.include_router(inventory.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(customers.router)


if store.using_database():
    @app.middleware("http")
    async def refresh_overrides(request, call_next):
        """Serverless: each request may run in a fresh process with its own
        memory, so re-read the edited costs before serving one. Skipped for
        static assets — only API responses depend on them."""
        if request.url.path.startswith("/api/"):
            store.load_overrides()
        return await call_next(request)


@app.get("/api/health")
def health():
    return {"status": "ok", "overrides_store": "postgres" if store.using_database() else "file"}


# ---------------------------------------------------------------------------
# Serve the built frontend from this same process, so the whole app is ONE
# thing to deploy on ONE port. In dev, `npm run dev` proxies /api here instead
# and this block is simply inactive (no dist/ yet).
# ---------------------------------------------------------------------------
_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if (_DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        """Serve a real built file if it exists, else index.html so react-router
        handles deep links like /menu on a hard refresh."""
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        f = (_DIST / path).resolve()
        if f.is_file() and f.is_relative_to(_DIST):
            return FileResponse(f)
        return FileResponse(_DIST / "index.html")
