"""Deal Profit Optimizer — CLAUDE.md §7.2, the Promolytics heart."""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from app.data import store
from app.logic import profit
from app.models.schemas import DealAssumptionsUpdate
from .common import date_range_params, get_filtered_orders

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("")
def list_deals(params: dict = Depends(date_range_params)):
    return profit.rank_deals(get_filtered_orders(params))


@router.get("/{deal_id}")
def get_deal(deal_id: str, params: dict = Depends(date_range_params)):
    if deal_id not in store.deals():
        raise HTTPException(404, "deal not found")
    return profit.deal_true_profit_stats(deal_id, get_filtered_orders(params))


@router.get("/{deal_id}/whatif")
def whatif(deal_id: str, incremental_fraction: float, attach_effect: float,
           params: dict = Depends(date_range_params)):
    """Live what-if: recompute true profit with hypothetical assumptions
    WITHOUT persisting them (CLAUDE.md §7.2 'what-if control')."""
    if deal_id not in store.deals():
        raise HTTPException(404, "deal not found")
    return profit.deal_true_profit_stats(deal_id, get_filtered_orders(params),
                                          incremental_fraction=incremental_fraction,
                                          attach_effect=attach_effect)


@router.patch("/{deal_id}/assumptions")
def update_assumptions(deal_id: str, body: DealAssumptionsUpdate):
    if deal_id not in store.deals():
        raise HTTPException(404, "deal not found")
    store.set_deal_assumptions(deal_id, body.incremental_fraction, body.attach_effect)
    return profit.deal_true_profit_stats(deal_id, store.orders())
