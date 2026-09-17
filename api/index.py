"""Vercel serverless entrypoint — exposes the same FastAPI app as local dev.

Vercel's Python runtime imports `app` from this file. The real application
lives in backend/app; nothing here duplicates it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402

__all__ = ["app"]
