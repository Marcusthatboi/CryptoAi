"""
Subscription and Stripe integration module for CryptoAI
Handles subscription tiers, pricing, and Stripe payments
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
import os
import json
from dotenv import load_dotenv
import logging
import stripe

load_dotenv()
logger = logging.getLogger(__name__)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_mock")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY


def has_insecure_stripe_config() -> bool:
    """Return True when Stripe is configured with placeholder credentials."""
    return (
        not STRIPE_SECRET_KEY
        or not STRIPE_PUBLISHABLE_KEY
        or STRIPE_SECRET_KEY == "sk_test_mock"
        or STRIPE_PUBLISHABLE_KEY == "pk_test_mock"
    )

# Subscription pricing
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "features": [
            "Basic investment tracking",
            "General AI recommendations",
            "Standard buy/sell lines",
            "Portfolio dashboard"
        ],
        "limits": {
            "signals_per_day": 20,
            "signals_total": 20,
            "alerts": True,
            "alert_limit": 15,
            "api_calls_per_hour": 20,
            "history_days": 0
        }
    },
    "pro": {
        "name": "Pro",
        "price": 999,  # $9.99 in cents
        "price_display": "$9.99/mo",
        "stripe_price_id": "price_pro_monthly",
        "features": [
            "Everything in Free +",
            "Advanced AI signals",
            "Real-time price alerts",
            "Signal confidence scoring",
            "Signal history (30 days)",
            "Portfolio optimization tips"
        ],
        "limits": {
            "signals_per_day": 60,
            "signals_total": None,
            "alerts": True,
            "alert_limit": 35,
            "api_calls_per_hour": 200,
            "history_days": 30
        }
    },
    "premium": {
        "name": "Premium",
        "price": 2999,  # $29.99 in cents
        "price_display": "$29.99/mo",
        "stripe_price_id": "price_premium_monthly",
        "features": [
            "Everything in Pro +",
            "Exclusive high-accuracy signals",
            "Unlimited alerts",
            "Signal history (1 year)",
            "Advanced portfolio analytics",
            "Early access to new features",
            "Priority support",
            "Performance tracking"
        ],
        "limits": {
            "signals_per_day": None,  # Unlimited
            "signals_total": None,
            "alerts": True,
            "alert_limit": None,  # Unlimited
            "api_calls_per_hour": 1000,
            "history_days": 365
        }
    }
}


# ============================================================================
# Pydantic Models
# ============================================================================

class SubscriptionTier(BaseModel):
    """Subscription tier model"""
    tier: str  # free, pro, premium
    name: str
    price: int  # in cents
    features: List[str]
    limits: Dict[str, Any]


class SubscriptionStatus(BaseModel):
    """User subscription status"""
    user_id: str
    tier: str
    status: str  # active, cancelled, expired
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    created_at: str
    updated_at: str


class PricingPage(BaseModel):
    """Pricing page data"""
    plans: List[SubscriptionTier]
    popular_plan: str = "pro"


class PaymentIntent(BaseModel):
    """Stripe payment intent model"""
    client_secret: str
    amount: int
    tier: str


# ============================================================================
# Subscription Database Operations
# ============================================================================

async def init_subscription_collection(db: AsyncIOMotorDatabase):
    """Initialize subscription collection with indexes"""
    subscriptions_col = db["subscriptions"]
    
    # Create indexes
    await subscriptions_col.create_index("user_id", unique=True)
    await subscriptions_col.create_index("stripe_customer_id")
    await subscriptions_col.create_index("stripe_subscription_id")
    await subscriptions_col.create_index("status")
    
    logger.info("✅ Subscription collection initialized")


async def create_subscription(
    db: AsyncIOMotorDatabase,
    user_id: str,
    tier: str = "free"
) -> Dict:
    """Create a new subscription record for a user"""
    subscriptions_col = db["subscriptions"]
    
    subscription_doc = {
        "user_id": user_id,
        "tier": tier,
        "status": "active",
        "stripe_customer_id": None,
        "stripe_subscription_id": None,
        "stripe_payment_method_id": None,
        "current_period_start": datetime.utcnow().isoformat(),
        "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "cancel_at_period_end": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = await subscriptions_col.insert_one(subscription_doc)
    subscription_doc["_id"] = result.inserted_id
    
    return subscription_doc


async def get_user_subscription(db: AsyncIOMotorDatabase, user_id: str) -> Optional[Dict]:
    """Get a user's subscription"""
    subscriptions_col = db["subscriptions"]
    subscription = await subscriptions_col.find_one({"user_id": user_id})
    return subscription


async def upgrade_subscription(
    db: AsyncIOMotorDatabase,
    user_id: str,
    new_tier: str,
    stripe_customer_id: str,
    stripe_subscription_id: str,
    stripe_payment_method_id: Optional[str] = None
) -> Dict:
    """Upgrade or change a user's subscription"""
    subscriptions_col = db["subscriptions"]
    
    now = datetime.utcnow()
    update_doc = {
        "tier": new_tier,
        "status": "active",
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "current_period_start": now.isoformat(),
        "current_period_end": (now + timedelta(days=30)).isoformat(),
        "cancel_at_period_end": False,
        "updated_at": now.isoformat()
    }
    
    if stripe_payment_method_id:
        update_doc["stripe_payment_method_id"] = stripe_payment_method_id
    
    result = await subscriptions_col.update_one(
        {"user_id": user_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Return updated subscription
    return await subscriptions_col.find_one({"user_id": user_id})


async def cancel_subscription(db: AsyncIOMotorDatabase, user_id: str) -> Dict:
    """Cancel a user's subscription"""
    subscriptions_col = db["subscriptions"]
    
    result = await subscriptions_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "status": "cancelled",
                "tier": "free",
                "cancel_at_period_end": True,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return await subscriptions_col.find_one({"user_id": user_id})


# ============================================================================
# Stripe Integration
# ============================================================================

async def create_stripe_customer(email: str, username: str) -> str:
    """Create a Stripe customer"""
    try:
        customer = stripe.Customer.create(
            email=email,
            name=username
        )
        return customer.id
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create payment customer: {str(e)}"
        )


async def create_payment_intent(
    customer_id: str,
    tier: str,
    email: str,
    user_id: Optional[str] = None
) -> Dict:
    """Create a Stripe payment intent for subscription"""
    try:
        plan = SUBSCRIPTION_PLANS.get(tier)
        if not plan or tier == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription tier"
            )
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=plan["price"],
            currency="usd",
            customer=customer_id,
            description=f"CryptoAI {plan['name']} Subscription",
            metadata={
                "tier": tier,
                "email": email,
                "user_id": user_id or ""
            }
        )
        
        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "amount": intent.amount,
            "currency": intent.currency,
            "tier": tier
        }
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create payment intent: {str(e)}"
        )


async def create_trade_payment_intent(
    customer_id: str,
    amount_cents: int,
    email: str,
    user_id: str,
    symbol: str,
    asset_class: str,
    quantity: float,
) -> Dict[str, Any]:
    """Create a Stripe payment intent for a live trade purchase."""
    try:
        if amount_cents <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trade amount must be greater than 0"
            )

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            customer=customer_id,
            description=f"CryptoAI Live Trade Purchase ({symbol.upper()})",
            metadata={
                "payment_purpose": "real_trade",
                "email": email,
                "user_id": user_id,
                "symbol": str(symbol or "").upper(),
                "asset_class": str(asset_class or "crypto").lower(),
                "quantity": str(quantity),
            }
        )

        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
        }
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating trade payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create trade payment intent: {str(e)}"
        )


async def verify_trade_payment_intent(
    payment_intent_id: str,
    user_id: str,
    minimum_amount_cents: int,
) -> Dict[str, Any]:
    """Verify a successful Stripe payment intent belongs to the requesting user and amount."""
    try:
        if not payment_intent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="payment_intent_id is required"
            )

        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if not intent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment intent not found"
            )

        if intent.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment intent is not succeeded (status: {intent.status})"
            )

        metadata = intent.metadata or {}
        intent_user_id = str(metadata.get("user_id", ""))
        if intent_user_id != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment intent does not belong to this user"
            )

        if str(metadata.get("payment_purpose", "")) != "real_trade":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment intent is not valid for live trade purchases"
            )

        amount_received = int(getattr(intent, "amount_received", 0) or 0)
        if amount_received < int(minimum_amount_cents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount is lower than required trade amount"
            )

        return {
            "payment_intent_id": intent.id,
            "amount": int(intent.amount or 0),
            "amount_received": amount_received,
            "currency": str(intent.currency or "usd"),
            "status": intent.status,
            "metadata": dict(metadata),
        }
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying trade payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify trade payment intent: {str(e)}"
        )


async def create_trade_refund(
    payment_intent_id: str,
    reason: str = "requested_by_customer",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Stripe refund for a live trade payment intent."""
    try:
        if not payment_intent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="payment_intent_id is required"
            )

        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            reason=reason,
            metadata={k: str(v) for k, v in (metadata or {}).items()}
        )

        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": int(refund.amount or 0),
            "currency": str(refund.currency or "usd"),
            "payment_intent_id": payment_intent_id,
        }
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating trade refund: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create trade refund: {str(e)}"
        )


async def create_checkout_session(
    customer_id: str,
    tier: str,
    email: str,
    success_url: str,
    cancel_url: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a Stripe-hosted checkout session suitable for Apple Pay on mobile devices."""
    try:
        plan = SUBSCRIPTION_PLANS.get(tier)
        if not plan or tier == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription tier"
            )

        session = stripe.checkout.Session.create(
            mode="payment",
            customer=customer_id,
            customer_email=email,
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method_types=["card"],
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": plan["price"],
                        "product_data": {
                            "name": f"CryptoAI {plan['name']} Subscription",
                            "description": f"Monthly tier upgrade to {plan['name']}"
                        }
                    }
                }
            ],
            metadata={
                "tier": tier,
                "email": email,
                "user_id": user_id or ""
            },
            payment_intent_data={
                "description": f"CryptoAI {plan['name']} Subscription",
                "metadata": {
                    "tier": tier,
                    "email": email,
                    "user_id": user_id or ""
                }
            }
        )

        return {
            "session_id": session.id,
            "url": session.url,
            "amount": plan["price"],
            "currency": "usd",
            "tier": tier
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create Apple Pay checkout session: {str(e)}"
        )


# ============================================================================
# Stripe Webhook Processing
# ============================================================================

def construct_stripe_webhook_event(payload: bytes, stripe_signature: Optional[str]) -> Dict[str, Any]:
    """Validate and construct a Stripe webhook event from request payload."""
    try:
        if STRIPE_WEBHOOK_SECRET:
            if not stripe_signature:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing Stripe-Signature header"
                )

            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=STRIPE_WEBHOOK_SECRET
            )
            return event

        # Dev fallback if webhook secret is not configured.
        logger.warning("STRIPE_WEBHOOK_SECRET not set; webhook signature verification skipped")
        return json.loads(payload.decode("utf-8"))
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Stripe signature: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(e)}"
        )


def _tier_from_price_id(price_id: Optional[str]) -> Optional[str]:
    if not price_id:
        return None

    for tier, details in SUBSCRIPTION_PLANS.items():
        if details.get("stripe_price_id") == price_id:
            return tier
    return None


async def _ensure_subscription(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, Any]:
    existing = await get_user_subscription(db, user_id)
    if existing:
        return existing
    return await create_subscription(db, user_id, "free")


async def process_stripe_webhook_event(
    db: AsyncIOMotorDatabase,
    event: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a Stripe webhook event and reconcile subscription state."""
    event_type = event.get("type", "unknown")
    data_object = (event.get("data") or {}).get("object") or {}
    subscriptions_col = db["subscriptions"]

    if event_type == "payment_intent.succeeded":
        metadata = data_object.get("metadata") or {}
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        customer_id = data_object.get("customer")
        payment_intent_id = data_object.get("id")
        payment_method_id = data_object.get("payment_method")

        if not user_id:
            if customer_id:
                existing = await subscriptions_col.find_one({"stripe_customer_id": customer_id})
                user_id = (existing or {}).get("user_id")

        if not user_id or not tier:
            logger.warning(f"Ignoring webhook {event_type}: missing user_id/tier metadata")
            return {"processed": False, "event_type": event_type, "reason": "missing_metadata"}

        await _ensure_subscription(db, user_id)

        now = datetime.utcnow()
        await subscriptions_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "tier": tier,
                    "status": "active",
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": payment_intent_id,
                    "stripe_payment_method_id": payment_method_id,
                    "current_period_start": now.isoformat(),
                    "current_period_end": (now + timedelta(days=30)).isoformat(),
                    "cancel_at_period_end": False,
                    "updated_at": now.isoformat()
                }
            }
        )
        return {"processed": True, "event_type": event_type, "user_id": user_id, "tier": tier}

    if event_type == "payment_intent.payment_failed":
        metadata = data_object.get("metadata") or {}
        user_id = metadata.get("user_id")
        customer_id = data_object.get("customer")

        if not user_id and customer_id:
            existing = await subscriptions_col.find_one({"stripe_customer_id": customer_id})
            user_id = (existing or {}).get("user_id")

        if user_id:
            await subscriptions_col.update_one(
                {"user_id": user_id},
                {"$set": {"status": "past_due", "updated_at": datetime.utcnow().isoformat()}}
            )
        return {"processed": True, "event_type": event_type, "user_id": user_id}

    if event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
        customer_id = data_object.get("customer")
        stripe_subscription_id = data_object.get("id")
        status_value = data_object.get("status") or "active"

        price_id = None
        items = ((data_object.get("items") or {}).get("data") or [])
        if items:
            price_id = ((items[0] or {}).get("price") or {}).get("id")

        mapped_tier = _tier_from_price_id(price_id)
        cancel_at_period_end = data_object.get("cancel_at_period_end", False)

        period_start = data_object.get("current_period_start")
        period_end = data_object.get("current_period_end")

        update_doc: Dict[str, Any] = {
            "status": status_value,
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "cancel_at_period_end": cancel_at_period_end,
            "updated_at": datetime.utcnow().isoformat()
        }

        if mapped_tier:
            update_doc["tier"] = mapped_tier
        if period_start:
            update_doc["current_period_start"] = datetime.utcfromtimestamp(period_start).isoformat()
        if period_end:
            update_doc["current_period_end"] = datetime.utcfromtimestamp(period_end).isoformat()

        if event_type == "customer.subscription.deleted":
            update_doc["tier"] = "free"
            update_doc["status"] = "cancelled"

        await subscriptions_col.update_one(
            {"stripe_customer_id": customer_id},
            {"$set": update_doc}
        )
        return {"processed": True, "event_type": event_type, "customer_id": customer_id}

    return {"processed": False, "event_type": event_type, "reason": "ignored"}


async def create_subscription_with_stripe(
    customer_id: str,
    tier: str,
    payment_method_id: str
) -> Dict:
    """Create a Stripe subscription"""
    try:
        plan = SUBSCRIPTION_PLANS.get(tier)
        if not plan or tier == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription tier"
            )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": plan["stripe_price_id"]}],
            default_payment_method=payment_method_id,
            billing_cycle_anchor=int(datetime.utcnow().timestamp())
        )
        
        return {
            "stripe_subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(
                subscription.current_period_start
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                subscription.current_period_end
            ).isoformat()
        }
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create subscription: {str(e)}"
        )


# ============================================================================
# Feature Access Control
# ============================================================================

def check_feature_access(subscription_tier: str, feature: str) -> bool:
    """Check if a user's subscription has access to a feature"""
    plan = SUBSCRIPTION_PLANS.get(subscription_tier, SUBSCRIPTION_PLANS["free"])
    
    feature_map = {
        "alerts": plan["limits"]["alerts"],
        "advanced_signals": subscription_tier in ["pro", "premium"],
        "signal_history": plan["limits"]["history_days"] > 0,
        "portfolio_optimization": subscription_tier in ["pro", "premium"],
        "early_access": subscription_tier == "premium",
        "priority_support": subscription_tier == "premium",
        "unlimited_signals": subscription_tier == "premium"
    }
    
    return feature_map.get(feature, False)


def get_usage_limit(subscription_tier: str, limit_type: str) -> Optional[int]:
    """Get usage limit for a feature"""
    plan = SUBSCRIPTION_PLANS.get(subscription_tier, SUBSCRIPTION_PLANS["free"])
    return plan["limits"].get(limit_type)


def has_quota_available(subscription_tier: str, usage_count: int, limit_type: str) -> bool:
    """Check if user has quota available"""
    limit = get_usage_limit(subscription_tier, limit_type)
    
    if limit is None:  # Unlimited
        return True
    
    return usage_count < limit


# ============================================================================
# Pricing Information
# ============================================================================

def get_all_pricing_plans() -> List[Dict]:
    """Get all pricing plans for display"""
    plans = []
    
    for tier_key, tier_data in SUBSCRIPTION_PLANS.items():
        if tier_key != "free":  # Only paid plans
            plans.append({
                "tier": tier_key,
                "name": tier_data["name"],
                "price": tier_data["price"],
                "price_display": tier_data.get("price_display", "$0.00"),
                "features": tier_data["features"],
                "popular": tier_key == "pro"
            })
    
    return plans


def get_tier_benefits(tier: str) -> Dict:
    """Get benefits for a specific tier"""
    plan = SUBSCRIPTION_PLANS.get(tier, SUBSCRIPTION_PLANS["free"])
    return {
        "name": plan["name"],
        "features": plan["features"],
        "limits": plan["limits"]
    }
