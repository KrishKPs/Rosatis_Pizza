"""Shared query-param handling: every module filters the same order list by
an optional date range + channel, so the parsing lives in one place."""

from __future__ import annotations
from datetime import date

from fastapi import Query

from app.data import store
from app.logic import profit


def date_range_params(
    start: date | None = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    channel: str | None = Query(default=None, description="Filter to one channel id"),
):
    return {"start": start, "end": end, "channel": channel}


def get_filtered_orders(params: dict):
    return profit.filter_orders(store.orders(), start=params["start"], end=params["end"],
                                 channel=params["channel"])
