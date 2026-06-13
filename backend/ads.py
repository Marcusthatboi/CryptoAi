"""
Self-hosted ad routing for CryptoAI.

Provides a simple sponsored-campaign feed, click tracking, and
Stripe-funded campaign checkout so the site can run first-party ads
without depending on an external ad network.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from bson import ObjectId
import stripe

from backend.auth import decode_token, get_user_by_id
from backend.db import get_db
from backend.subscription import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    construct_stripe_webhook_event,
    has_insecure_stripe_config,
)

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/api/ads", tags=["ads"])
logger = logging.getLogger(__name__)

CAMPAIGNS_COLLECTION = "ad_campaigns"
EVENTS_COLLECTION = "ad_events"
DEFAULT_PLACEMENT = "home"


DEFAULT_CAMPAIGNS: List[Dict[str, Any]] = [
    {
        "title": "List Your Project on DaCryptoBeast",
        "description": "Run a self-hosted campaign with pay-per-click tracking and Stripe-funded budget control.",
        "url": "https://dacryptobeast.com/pricing",
        "image": "",
        "placement": "home",
        "sponsor_name": "CryptoAI Ads",
        "cpc_cents": 25,
        "budget_cents": 2500,
    },
    {
        "title": "Promote Your Token Launch",
        "description": "Reach crypto traders with a click-tracked sponsored slot on the dashboard.",
        "url": "https://dacryptobeast.com/tools",
        "image": "",
        "placement": "home",
        "sponsor_name": "CryptoAI Ads",
        "cpc_cents": 35,
        "budget_cents": 3500,
    },
]


class AdCampaignCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    description: str = Field(..., min_length=2, max_length=240)
    url: str = Field(..., min_length=5)
    image: str = ""
    placement: str = Field(default=DEFAULT_PLACEMENT, min_length=2, max_length=50)
    sponsor_name: str = Field(default="CryptoAI Ads", min_length=2, max_length=120)
    cpc_cents: int = Field(default=25, ge=1)
    budget_cents: int = Field(default=2500, ge=1)


class AdCheckoutRequest(BaseModel):
    success_url: str = Field(..., min_length=10)
    cancel_url: str = Field(..., min_length=10)
    amount_cents: Optional[int] = Field(default=None, ge=1)


def _utcnow() -> datetime:
    return datetime.utcnow()


def _campaign_is_active(campaign: Dict[str, Any]) -> bool:
    return (
        str(campaign.get("status", "active")).lower() == "active"
        and int(campaign.get("remaining_budget_cents", 0) or 0) > 0
    )


def _to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(str(value))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign id")


def _serialize_campaign(campaign: Dict[str, Any], request: Request) -> Dict[str, Any]:
    campaign_id = str(campaign.get("_id"))
    base_url = str(request.base_url).rstrip("/")

    return {
        "id": campaign_id,
        "title": campaign.get("title", "Sponsored"),
        "description": campaign.get("description", ""),
        "url": campaign.get("url", "#"),
        "tracking_url": f"{base_url}/api/ads/campaigns/{campaign_id}/click",
        "image": campaign.get("image", ""),
        "placement": campaign.get("placement", DEFAULT_PLACEMENT),
        "sponsor_name": campaign.get("sponsor_name", "CryptoAI Ads"),
        "cpc_cents": int(campaign.get("cpc_cents", 0) or 0),
        "budget_cents": int(campaign.get("budget_cents", 0) or 0),
        "remaining_budget_cents": int(campaign.get("remaining_budget_cents", 0) or 0),
        "clicks": int(campaign.get("clicks", 0) or 0),
        "impressions": int(campaign.get("impressions", 0) or 0),
    }


async def _get_campaigns_col(db: AsyncIOMotorDatabase):
    return db[CAMPAIGNS_COLLECTION]


async def _get_events_col(db: AsyncIOMotorDatabase):
    return db[EVENTS_COLLECTION]


async def _seed_default_campaigns(db: AsyncIOMotorDatabase) -> None:
    campaigns_col = await _get_campaigns_col(db)
    if await campaigns_col.count_documents({}) > 0:
        return

    now = _utcnow()
    documents = []
    for campaign in DEFAULT_CAMPAIGNS:
        documents.append(
            {
                **campaign,
                "status": "active",
                "remaining_budget_cents": int(campaign["budget_cents"]),
                "clicks": 0,
                "impressions": 0,
                "created_at": now,
                "updated_at": now,
                "funding_source": "seed",
            }
        )

    if documents:
        await campaigns_col.insert_many(documents)


async def _verify_admin_user(
    authorization: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    payload = decode_token(token)
    user_id = payload.get("sub")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    username = str(user.get("username", "")).strip().lower()
    role = str(user.get("role", "")).strip().lower()
    admin_username = os.getenv("ADMIN_USERNAME", "dacryptobeast_admin").strip().lower()

    if role != "admin" and username not in {"admin", admin_username}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return user


@router.get("/placements/{placement}")
async def get_placement_ads(
    placement: str,
    limit: int = 2,
    request: Request = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    campaigns_col = await _get_campaigns_col(db)
    await _seed_default_campaigns(db)

    query = {
        "placement": placement,
        "status": "active",
        "remaining_budget_cents": {"$gt": 0},
    }

    campaigns = await campaigns_col.find(query).sort([("remaining_budget_cents", -1), ("updated_at", -1)]).limit(max(1, min(int(limit or 2), 10))).to_list(length=max(1, min(int(limit or 2), 10)))

    if not campaigns and placement != DEFAULT_PLACEMENT:
        campaigns = await campaigns_col.find({
            "placement": DEFAULT_PLACEMENT,
            "status": "active",
            "remaining_budget_cents": {"$gt": 0},
        }).sort([("remaining_budget_cents", -1), ("updated_at", -1)]).limit(max(1, min(int(limit or 2), 10))).to_list(length=max(1, min(int(limit or 2), 10)))

    if request is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Request context is unavailable")

    serialized = [_serialize_campaign(campaign, request) for campaign in campaigns]
    return {"placement": placement, "ads": serialized}


@router.post("/campaigns")
async def create_campaign(
    payload: AdCampaignCreate,
    admin_user: Dict[str, Any] = Depends(_verify_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    campaigns_col = await _get_campaigns_col(db)
    now = _utcnow()
    document = {
        "title": payload.title,
        "description": payload.description,
        "url": payload.url,
        "image": payload.image,
        "placement": payload.placement,
        "sponsor_name": payload.sponsor_name,
        "cpc_cents": int(payload.cpc_cents),
        "budget_cents": int(payload.budget_cents),
        "remaining_budget_cents": 0,
        "status": "draft",
        "clicks": 0,
        "impressions": 0,
        "funding_source": "stripe",
        "created_at": now,
        "updated_at": now,
        "created_by": str(admin_user.get("_id")),
    }
    result = await campaigns_col.insert_one(document)
    document["_id"] = result.inserted_id
    return {
        "campaign": {
            "id": str(document["_id"]),
            "title": document["title"],
            "placement": document["placement"],
            "status": document["status"],
            "budget_cents": document["budget_cents"],
            "cpc_cents": document["cpc_cents"],
        }
    }


@router.get("/campaigns")
async def list_campaigns(
    admin_user: Dict[str, Any] = Depends(_verify_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    del admin_user

    campaigns_col = await _get_campaigns_col(db)
    await _seed_default_campaigns(db)

    campaigns = await campaigns_col.find({}).sort([("updated_at", -1)]).to_list(length=100)
    serialized = [
        {
            "id": str(campaign.get("_id")),
            "title": campaign.get("title", "Sponsored"),
            "description": campaign.get("description", ""),
            "url": campaign.get("url", "#"),
            "placement": campaign.get("placement", DEFAULT_PLACEMENT),
            "sponsor_name": campaign.get("sponsor_name", "CryptoAI Ads"),
            "status": campaign.get("status", "draft"),
            "cpc_cents": int(campaign.get("cpc_cents", 0) or 0),
            "budget_cents": int(campaign.get("budget_cents", 0) or 0),
            "remaining_budget_cents": int(campaign.get("remaining_budget_cents", 0) or 0),
            "clicks": int(campaign.get("clicks", 0) or 0),
            "impressions": int(campaign.get("impressions", 0) or 0),
            "updated_at": campaign.get("updated_at"),
            "created_at": campaign.get("created_at"),
        }
        for campaign in campaigns
    ]

    return {"campaigns": serialized}


@router.post("/campaigns/{campaign_id}/stripe-checkout-session")
async def create_campaign_checkout_session(
    campaign_id: str,
    payload: AdCheckoutRequest,
    admin_user: Dict[str, Any] = Depends(_verify_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if has_insecure_stripe_config():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured for checkout")

    campaigns_col = await _get_campaigns_col(db)
    campaign = await campaigns_col.find_one({"_id": _to_object_id(campaign_id)})
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    amount_cents = int(payload.amount_cents or campaign.get("budget_cents") or 0)
    if amount_cents <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Checkout amount must be greater than 0")

    customer = stripe.Customer.create(
        email=str(admin_user.get("email", "")) or None,
        name=str(admin_user.get("username", "CryptoAI Ads")),
    )

    session = stripe.checkout.Session.create(
        mode="payment",
        customer=customer.id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        payment_method_types=["card"],
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"Sponsored campaign funding: {campaign.get('title', 'CryptoAI Ads')}",
                        "description": f"Fund pay-per-click ads for placement '{campaign.get('placement', DEFAULT_PLACEMENT)}'",
                    },
                },
            }
        ],
        metadata={
            "campaign_id": campaign_id,
            "placement": str(campaign.get("placement", DEFAULT_PLACEMENT)),
            "payment_purpose": "ad_campaign_funding",
        },
        payment_intent_data={
            "metadata": {
                "campaign_id": campaign_id,
                "placement": str(campaign.get("placement", DEFAULT_PLACEMENT)),
                "payment_purpose": "ad_campaign_funding",
            }
        },
    )

    await campaigns_col.update_one(
        {"_id": _to_object_id(campaign_id)},
        {
            "$set": {
                "status": "pending_payment",
                "stripe_customer_id": customer.id,
                "stripe_checkout_session_id": session.id,
                "updated_at": _utcnow(),
            }
        },
    )

    return {"session_id": session.id, "url": session.url, "amount": amount_cents, "currency": "usd"}


@router.post("/campaigns/{campaign_id}/click")
async def record_campaign_click(
    campaign_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    campaigns_col = await _get_campaigns_col(db)
    events_col = await _get_events_col(db)
    campaign = await campaigns_col.find_one({"_id": _to_object_id(campaign_id)})

    if not campaign or not _campaign_is_active(campaign):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not available")

    cpc_cents = int(campaign.get("cpc_cents", 0) or 0)
    remaining_budget = max(0, int(campaign.get("remaining_budget_cents", 0) or 0) - cpc_cents)
    next_status = "active" if remaining_budget > 0 else "exhausted"

    await campaigns_col.update_one(
        {"_id": _to_object_id(campaign_id)},
        {
            "$inc": {"clicks": 1},
            "$set": {
                "remaining_budget_cents": remaining_budget,
                "status": next_status,
                "updated_at": _utcnow(),
            },
        },
    )

    await events_col.insert_one(
        {
            "campaign_id": campaign_id,
            "event_type": "click",
            "placement": campaign.get("placement", DEFAULT_PLACEMENT),
            "created_at": _utcnow(),
            "user_agent": request.headers.get("user-agent", ""),
            "referrer": request.headers.get("referer", ""),
        }
    )

    return RedirectResponse(url=str(campaign.get("url", "#")), status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.post("/webhook/stripe")
async def handle_stripe_webhook(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    payload = await request.body()
    stripe_signature = request.headers.get("Stripe-Signature")

    event = construct_stripe_webhook_event(payload, stripe_signature)
    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    campaigns_col = await _get_campaigns_col(db)

    if event_type == "checkout.session.completed":
        metadata = data_object.get("metadata", {}) or {}
        campaign_id = str(metadata.get("campaign_id", ""))
        payment_intent = data_object.get("payment_intent", "")
        amount_total = int(data_object.get("amount_total", 0) or 0)

        if campaign_id:
            await campaigns_col.update_one(
                {"_id": _to_object_id(campaign_id)},
                {
                    "$set": {
                        "status": "active",
                        "budget_cents": amount_total,
                        "remaining_budget_cents": amount_total,
                        "stripe_payment_intent_id": payment_intent,
                        "stripe_checkout_session_id": data_object.get("id", ""),
                        "updated_at": _utcnow(),
                    }
                },
            )

    return JSONResponse({"status": "ok", "event_type": event_type})