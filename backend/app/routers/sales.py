"""Sales & Analytics — CLAUDE.md §7.1, the home screen."""

from __future__ import annotations
from fastapi import APIRouter, Depends

from app.logic import profit
from .common import date_range_params, get_filtered_orders

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("/summary")
def summary(params: dict = Depends(date_range_params)):
    return profit.sales_summary(get_filtered_orders(params))


@router.get("/timeseries")
def timeseries(params: dict = Depends(date_range_params)):
    return profit.revenue_profit_over_time(get_filtered_orders(params))


@router.get("/by-category")
def by_category(params: dict = Depends(date_range_params)):
    return profit.sales_by_category(get_filtered_orders(params))


@router.get("/by-channel")
def by_channel(params: dict = Depends(date_range_params)):
    return profit.channel_profit_summary(get_filtered_orders(params))


@router.get("/heatmap")
def heatmap(params: dict = Depends(date_range_params)):
    return profit.day_hour_heat(get_filtered_orders(params))


@router.get("/top-items")
def top_items(n: int = 10, params: dict = Depends(date_range_params)):
    return profit.top_items(get_filtered_orders(params), n=n)
