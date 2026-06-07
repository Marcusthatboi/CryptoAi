"""
Subscription API routes for CryptoAI
Handles subscription upgrades, payments, and status checks
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse
from typing import Optional
from backend.subscription import (
    get_all_pricing_plans,
    get_tier_benefits,
    create_stripe_customer,
    create_payment_intent,
    create_subscription_with_stripe,
    get_user_subscription,
    upgrade_subscription,
    cancel_subscription,
    create_subscription,
    SubscriptionStatus,
    PricingPage
)
from backend.auth import decode_token, get_user_by_id
from backend.db import get_db
import logging

router = APIRouter(prefix="/api/subscription", tags=["subscription"])
logger = logging.getLogger(__name__)


# ============================================================================
# Dependencies
# ============================================================================

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
        return decode_token(token)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )


# ============================================================================
# Public Routes
# ============================================================================

@router.get("/pricing/plans", response_model=PricingPage)
async def get_pricing_plans():
    """Get all pricing plans"""
    try:
        plans = get_all_pricing_plans()
        return {
            "plans": plans,
            "popular_plan": "pro"
        }
    except Exception as e:
        logger.error(f"Error fetching pricing plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pricing plans"
        )


@router.get("/benefits/{tier}")
async def get_tier_benefits_info(tier: str):
    """Get benefits for a specific subscription tier"""
    if tier not in ["free", "pro", "premium"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier"
        )
    
    try:
        benefits = get_tier_benefits(tier)
        return benefits
    except Exception as e:
        logger.error(f"Error fetching tier benefits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tier benefits"
        )


# ============================================================================
# Protected Routes
# ============================================================================

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    token_payload: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get user's current subscription status"""
    try:
        user_id = token_payload.get("sub")
        
        subscription = await get_user_subscription(db, user_id)
        
        if not subscription:
            # Create default free subscription if none exists
            subscription = await create_subscription(db, user_id, "free")
        
        return {
            "user_id": subscription.get("user_id"),
            "tier": subscription.get("tier", "free"),
            "status": subscription.get("status", "active"),
            "stripe_customer_id": subscription.get("stripe_customer_id"),
            "stripe_subscription_id": subscription.get("stripe_subscription_id"),
            "current_period_start": subscription.get("current_period_start"),
            "current_period_end": subscription.get("current_period_end"),
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "created_at": subscription.get("created_at"),
            "updated_at": subscription.get("updated_at")
        }
    except Exception as e:
        logger.error(f"Error fetching subscription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription status"
        )


@router.post("/create-payment-intent")
async def create_payment_intent_endpoint(
    tier: str,
    token_payload: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Create a Stripe payment intent for upgrading subscription"""
    try:
        user_id = token_payload.get("sub")
        
        # Get user info
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        email = user.get("email", "noemail@cryptoai.com")
        
        # Get or create Stripe customer
        subscription = await get_user_subscription(db, user_id)
        
        if subscription and subscription.get("stripe_customer_id"):
            customer_id = subscription["stripe_customer_id"]
        else:
            customer_id = await create_stripe_customer(email, user.get("username"))
        
        # Create payment intent
        intent = await create_payment_intent(customer_id, tier, email)
        
        return intent
    
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}"
        )


@router.post("/upgrade")
async def upgrade_subscription_endpoint(
    tier: str,
    stripe_customer_id: str,
    stripe_subscription_id: str,
    payment_method_id: Optional[str] = None,
    token_payload: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Upgrade user subscription"""
    try:
        user_id = token_payload.get("sub")
        
        # Verify subscription exists, create if needed
        subscription = await get_user_subscription(db, user_id)
        if not subscription:
            subscription = await create_subscription(db, user_id, "free")
        
        # Upgrade subscription
        updated_subscription = await upgrade_subscription(
            db,
            user_id,
            tier,
            stripe_customer_id,
            stripe_subscription_id,
            payment_method_id
        )
        
        logger.info(f"User {user_id} upgraded to {tier} tier")
        
        return {
            "status": "success",
            "message": f"Successfully upgraded to {tier} plan",
            "subscription": {
                "user_id": updated_subscription.get("user_id"),
                "tier": updated_subscription.get("tier"),
                "status": updated_subscription.get("status"),
                "current_period_end": updated_subscription.get("current_period_end")
            }
        }
    
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade subscription: {str(e)}"
        )


@router.post("/cancel")
async def cancel_subscription_endpoint(
    token_payload: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Cancel user's subscription"""
    try:
        user_id = token_payload.get("sub")
        
        cancelled_subscription = await cancel_subscription(db, user_id)
        
        logger.info(f"User {user_id} cancelled subscription")
        
        return {
            "status": "success",
            "message": "Subscription cancelled successfully",
            "subscription": {
                "tier": cancelled_subscription.get("tier"),
                "status": cancelled_subscription.get("status")
            }
        }
    
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


# ============================================================================
# Webhook Routes (for Stripe events)
# ============================================================================

@router.post("/webhook/stripe")
async def handle_stripe_webhook(
    request_body: dict,
    db = Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        event_type = request_body.get("type")
        event_data = request_body.get("data", {}).get("object", {})
        
        if event_type == "customer.subscription.updated":
            # Update subscription status
            customer_id = event_data.get("customer")
            status_value = event_data.get("status")
            
            # Find user by stripe_customer_id and update
            subscriptions_col = db["subscriptions"]
            await subscriptions_col.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {"status": status_value}}
            )
            
            logger.info(f"Updated subscription status for customer {customer_id}")
        
        elif event_type == "customer.subscription.deleted":
            customer_id = event_data.get("customer")
            subscriptions_col = db["subscriptions"]
            await subscriptions_col.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {"status": "cancelled", "tier": "free"}}
            )
            
            logger.info(f"Cancelled subscription for customer {customer_id}")
        
        return {"status": "received"}
    
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )
