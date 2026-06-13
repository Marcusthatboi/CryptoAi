"""
Launch Promo Routes
===================
Handles the first-100-users 45% launch discount for Pro and Premium subscriptions.
Tracks claims, validates eligibility, and applies a verified discount to Stripe checkout.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.db import get_db
from backend.subscription import SUBSCRIPTION_PLANS, has_insecure_stripe_config

logger = logging.getLogger(__name__)

PROMO_MAX_CLAIMS = int(os.getenv("PROMO_LAUNCH_MAX_CLAIMS", "100"))
PROMO_DISCOUNT_PCT = int(os.getenv("PROMO_LAUNCH_DISCOUNT_PCT", "45"))
PROMO_ELIGIBLE_TIERS = {"pro", "premium"}
PROMO_CODE = os.getenv("PROMO_LAUNCH_CODE", "LAUNCH45")


class PromoStatusResponse(BaseModel):
    active: bool
    claims_remaining: int
    total_slots: int
    discount_pct: int
    code: str
    message: str


async def _get_promo_collection(db):
    return db["launch_promo_claims"]


async def get_promo_status(db) -> Dict[str, Any]:
    """Return current promo claim count and availability."""
    col = await _get_promo_collection(db)
    claimed = await col.count_documents({})
    remaining = max(0, PROMO_MAX_CLAIMS - claimed)
    return {
        "active": remaining > 0,
        "claims_used": claimed,
        "claims_remaining": remaining,
        "total_slots": PROMO_MAX_CLAIMS,
        "discount_pct": PROMO_DISCOUNT_PCT,
        "code": PROMO_CODE,
    }


async def claim_promo_for_user(
    db,
    user_id: str,
    tier: str,
) -> Dict[str, Any]:
    """
    Attempt to reserve a promo slot for a user.
    Returns the discounted amount in cents, or raises if not eligible.
    """
    tier_lower = str(tier or "").lower()
    if tier_lower not in PROMO_ELIGIBLE_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Launch promo is available for Pro and Premium tiers only",
        )

    col = await _get_promo_collection(db)

    existing = await col.find_one({"user_id": user_id, "tier": tier_lower})
    if existing:
        original = SUBSCRIPTION_PLANS[tier_lower]["price"]
        discount_amount = round(original * PROMO_DISCOUNT_PCT / 100)
        discounted = original - discount_amount
        return {
            "already_claimed": True,
            "discount_pct": PROMO_DISCOUNT_PCT,
            "original_cents": original,
            "discount_cents": discount_amount,
            "discounted_cents": discounted,
        }

    total = await col.count_documents({})
    if total >= PROMO_MAX_CLAIMS:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Launch promo is sold out. All 100 discounted spots have been claimed.",
        )

    now = datetime.now(timezone.utc).isoformat()
    await col.insert_one({
        "user_id": user_id,
        "tier": tier_lower,
        "claimed_at": now,
        "discount_pct": PROMO_DISCOUNT_PCT,
        "position": total + 1,
    })

    original = SUBSCRIPTION_PLANS[tier_lower]["price"]
    discount_amount = round(original * PROMO_DISCOUNT_PCT / 100)
    discounted = original - discount_amount

    logger.info(
        "Launch promo claimed: user=%s tier=%s position=%s discounted=%s cents",
        user_id, tier_lower, total + 1, discounted,
    )

    return {
        "already_claimed": False,
        "discount_pct": PROMO_DISCOUNT_PCT,
        "original_cents": original,
        "discount_cents": discount_amount,
        "discounted_cents": discounted,
        "position": total + 1,
    }


def create_promo_router(get_current_user_dependency, get_db_fn=get_db):
    router = APIRouter(prefix="/api/promo", tags=["promo"])

    @router.get("/status", response_model=PromoStatusResponse)
    async def promo_status(db=Depends(get_db_fn)):
        """Check current launch promo availability (public)."""
        s = await get_promo_status(db)
        msg = (
            f"🎉 {s['claims_remaining']} of {s['total_slots']} launch spots remaining — {s['discount_pct']}% off Pro & Premium!"
            if s["active"]
            else "Launch promo has ended. All spots have been claimed."
        )
        return PromoStatusResponse(
            active=s["active"],
            claims_remaining=s["claims_remaining"],
            total_slots=s["total_slots"],
            discount_pct=s["discount_pct"],
            code=s["code"],
            message=msg,
        )

    @router.post("/claim")
    async def claim_promo(
        tier: str,
        current_user: str = Depends(get_current_user_dependency),
        db=Depends(get_db_fn),
    ):
        """Claim a launch promo slot for the authenticated user."""
        result = await claim_promo_for_user(db, current_user, tier)
        return {"status": "ok", **result}

    return router
