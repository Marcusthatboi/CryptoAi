"""
Auto Trading Per-Cryptocurrency Routes
API endpoints for managing individual coin auto trading settings
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime
from backend.db import get_db
from backend.auto_trading_settings import (
    CryptoAutoTradingSettings,
    DEFAULT_BUY_PERCENTAGE,
    DEFAULT_SELL_PERCENTAGE,
)
from backend.subscription import get_user_subscription
import logging

logger = logging.getLogger(__name__)


async def verify_premium_subscription(current_user: Dict, db) -> Dict:
    """Verify user has premium subscription."""
    try:
        user_id = current_user if isinstance(current_user, str) else current_user.get("_id")
        subscription = await get_user_subscription(db, user_id)
        if not subscription:
            raise HTTPException(status_code=403, detail="Premium subscription required")
        tier = subscription.get("tier", "free").lower()
        if tier != "premium":
            raise HTTPException(status_code=403, detail=f"Premium required. Current: {tier}")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Premium check error: {e}")
        raise HTTPException(status_code=500, detail="Error verifying subscription")


def create_auto_trading_coin_router(get_current_user_dependency):
    """Factory function to create auto trading coin router"""
    router = APIRouter(prefix="/api/auto-trading-per-coin", tags=["auto-trading-coin"])

    @router.post("/enable/{symbol}")
    async def enable_auto_trading_for_coin(
        symbol: str,
        buy_percentage: Optional[float] = DEFAULT_BUY_PERCENTAGE,
        sell_percentage: Optional[float] = DEFAULT_SELL_PERCENTAGE,
        reference_price: Optional[float] = None,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Enable auto trading for a cryptocurrency"""
        await verify_premium_subscription(current_user, db)
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        if buy_percentage <= 0 or buy_percentage > 100:
            raise HTTPException(status_code=400, detail="Buy percentage must be 0-100")
        if sell_percentage <= 0 or sell_percentage > 100:
            raise HTTPException(status_code=400, detail="Sell percentage must be 0-100")

        try:
            auto_trade_db = db["auto_trading_settings"]
            existing = await auto_trade_db.find_one({"user_id": user_id, "symbol": symbol.upper()})
            now = datetime.utcnow().isoformat()

            if existing:
                await auto_trade_db.update_one(
                    {"user_id": user_id, "symbol": symbol.upper()},
                    {
                        "$set": {
                            "enabled": True,
                            "buy_percentage": buy_percentage,
                            "sell_percentage": sell_percentage,
                            "reference_price": reference_price or existing.get("reference_price"),
                            "updated_at": now,
                        },
                        "$push": {
                            "actions_history": {
                                "timestamp": now,
                                "action_type": "ENABLE",
                                "reason": f"Buy {buy_percentage}%, Sell {sell_percentage}%"
                            }
                        }
                    }
                )
                return {"status": "enabled", "symbol": symbol.upper(), "message": "Updated"}
            else:
                settings = CryptoAutoTradingSettings(
                    user_id=user_id,
                    symbol=symbol.upper(),
                    enabled=True,
                    buy_percentage=buy_percentage,
                    sell_percentage=sell_percentage,
                    reference_price=reference_price,
                    created_at=now,
                    updated_at=now,
                    actions_history=[{"timestamp": now, "action_type": "ENABLE", "reason": f"Buy {buy_percentage}%, Sell {sell_percentage}%"}]
                )
                await auto_trade_db.insert_one(settings.to_dict())
                return {"status": "enabled", "symbol": symbol.upper(), "message": "Created"}
        except Exception as e:
            logger.error(f"Enable error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.post("/disable/{symbol}")
    async def disable_auto_trading_for_coin(
        symbol: str,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Disable auto trading for a cryptocurrency"""
        await verify_premium_subscription(current_user, db)
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        try:
            auto_trade_db = db["auto_trading_settings"]
            now = datetime.utcnow().isoformat()
            result = await auto_trade_db.update_one(
                {"user_id": user_id, "symbol": symbol.upper()},
                {
                    "$set": {"enabled": False, "updated_at": now},
                    "$push": {"actions_history": {"timestamp": now, "action_type": "DISABLE", "reason": "Disabled by user"}}
                }
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail=f"Not configured for {symbol}")
            return {"status": "disabled", "symbol": symbol.upper(), "message": "Disabled"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Disable error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.get("/settings/{symbol}")
    async def get_auto_trading_settings(
        symbol: str,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Get auto trading settings for a cryptocurrency"""
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        try:
            auto_trade_db = db["auto_trading_settings"]
            settings = await auto_trade_db.find_one({"user_id": user_id, "symbol": symbol.upper()})

            if not settings:
                return {
                    "symbol": symbol.upper(),
                    "enabled": False,
                    "buy_percentage": DEFAULT_BUY_PERCENTAGE,
                    "sell_percentage": DEFAULT_SELL_PERCENTAGE,
                    "reference_price": None,
                    "average_cost": None,
                    "total_quantity_held": 0.0,
                    "total_profit_loss": 0.0,
                    "message": "Not configured"
                }

            settings.pop("_id", None)
            return settings
        except Exception as e:
            logger.error(f"Get settings error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.get("/active")
    async def get_all_active_auto_trades(
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Get all active auto trading configurations (optimized with projection)"""
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        try:
            auto_trade_db = db["auto_trading_settings"]
            # Optimize: exclude unnecessary fields and use projection
            active_trades = await auto_trade_db.find(
                {"user_id": user_id, "enabled": True},
                {
                    "_id": 0,
                    "symbol": 1,
                    "enabled": 1,
                    "buy_percentage": 1,
                    "sell_percentage": 1,
                    "reference_price": 1,
                    "total_profit_loss": 1,
                    "total_quantity_held": 1,
                    "average_cost": 1,
                    "updated_at": 1
                }
            ).to_list(None)

            return {"total_active": len(active_trades), "active_trades": active_trades}
        except Exception as e:
            logger.error(f"Get active error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.get("/history/{symbol}")
    async def get_auto_trade_history(
        symbol: str,
        limit: int = 50,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Get action history for a cryptocurrency"""
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        try:
            auto_trade_db = db["auto_trading_settings"]
            settings = await auto_trade_db.find_one({"user_id": user_id, "symbol": symbol.upper()})

            if not settings:
                raise HTTPException(status_code=404, detail=f"No data for {symbol}")

            history = settings.get("actions_history", [])
            history = history[-limit:] if limit else history
            history.reverse()

            return {
                "symbol": symbol.upper(),
                "total_actions": len(history),
                "history": history,
                "total_profit_loss": settings.get("total_profit_loss", 0.0),
                "average_cost": settings.get("average_cost"),
                "total_quantity_held": settings.get("total_quantity_held", 0.0)
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get history error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.get("/stats/{symbol}")
    async def get_auto_trade_stats(
        symbol: str,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Get performance statistics"""
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        try:
            auto_trade_db = db["auto_trading_settings"]
            settings = await auto_trade_db.find_one({"user_id": user_id, "symbol": symbol.upper()})

            if not settings:
                raise HTTPException(status_code=404, detail=f"No data for {symbol}")

            history = settings.get("actions_history", [])
            buy_count = sum(1 for a in history if a.get("action_type") == "BUY")
            sell_count = sum(1 for a in history if a.get("action_type") == "SELL")
            total_pl = settings.get("total_profit_loss", 0.0)
            win_count = sum(1 for a in history if a.get("action_type") == "SELL" and a.get("profit_loss", 0) > 0)

            return {
                "symbol": symbol.upper(),
                "enabled": settings.get("enabled", False),
                "buy_percentage": settings.get("buy_percentage", DEFAULT_BUY_PERCENTAGE),
                "sell_percentage": settings.get("sell_percentage", DEFAULT_SELL_PERCENTAGE),
                "total_buys": buy_count,
                "total_sells": sell_count,
                "winning_sells": win_count,
                "total_profit_loss": total_pl,
                "win_rate": f"{(win_count / sell_count * 100):.1f}%" if sell_count > 0 else "N/A",
                "average_cost": settings.get("average_cost"),
                "quantity_held": settings.get("total_quantity_held", 0.0),
                "last_action": settings.get("last_action"),
                "created_at": settings.get("created_at"),
                "updated_at": settings.get("updated_at")
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get stats error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.put("/update/{symbol}")
    async def update_auto_trading_settings(
        symbol: str,
        buy_percentage: Optional[float] = None,
        sell_percentage: Optional[float] = None,
        reference_price: Optional[float] = None,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Update auto trading settings"""
        await verify_premium_subscription(current_user, db)
        user_id = current_user if isinstance(current_user, str) else str(current_user.get("_id"))

        if buy_percentage is not None and (buy_percentage <= 0 or buy_percentage > 100):
            raise HTTPException(status_code=400, detail="Buy percentage must be 0-100")
        if sell_percentage is not None and (sell_percentage <= 0 or sell_percentage > 100):
            raise HTTPException(status_code=400, detail="Sell percentage must be 0-100")

        try:
            auto_trade_db = db["auto_trading_settings"]
            update_data = {"updated_at": datetime.utcnow().isoformat()}

            if buy_percentage is not None:
                update_data["buy_percentage"] = buy_percentage
            if sell_percentage is not None:
                update_data["sell_percentage"] = sell_percentage
            if reference_price is not None:
                update_data["reference_price"] = reference_price

            result = await auto_trade_db.update_one(
                {"user_id": user_id, "symbol": symbol.upper()},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail=f"Not configured for {symbol}")

            updated = await auto_trade_db.find_one({"user_id": user_id, "symbol": symbol.upper()})
            updated.pop("_id", None)

            return {"status": "updated", "symbol": symbol.upper(), "message": "Updated", "settings": updated}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

    @router.get("/recommendations/{symbol}")
    async def get_ai_recommendations(
        symbol: str,
        current_user: Dict = Depends(get_current_user_dependency),
        db = Depends(get_db)
    ):
        """Get AI-powered recommendations for buy/sell percentages and reference price"""
        await verify_premium_subscription(current_user, db)
        user_id = current_user if isinstance(current_user, str) else current_user.get("_id")

        try:
            auto_trade_db = db["auto_trading_settings"]
            settings = await auto_trade_db.find_one({"user_id": user_id, "symbol": symbol.upper()})
            
            # Generate AI recommendations based on volatility patterns
            # These are intelligent defaults based on market behavior
            volatility_score = 0.5  # Base volatility
            
            if settings and "actions_history" in settings and len(settings["actions_history"]) > 0:
                # Calculate volatility from trading history
                recent_actions = settings["actions_history"][-20:] if len(settings["actions_history"]) > 20 else settings["actions_history"]
                if recent_actions:
                    prices = [a.get("price", 0) for a in recent_actions if a.get("price")]
                    if len(prices) > 1:
                        avg_price = sum(prices) / len(prices)
                        price_range = max(prices) - min(prices)
                        volatility_score = (price_range / avg_price) if avg_price > 0 else 0.5
                        volatility_score = min(max(volatility_score, 0.1), 0.9)  # Clamp between 0.1 and 0.9

            # Generate recommendations based on volatility
            # Higher volatility = wider spreads
            if volatility_score < 0.2:
                # Low volatility: Tight spreads
                recommendations = {
                    "buy_percentage": 2.0,
                    "sell_percentage": 3.0,
                    "volatility_tier": "Low",
                    "reason": "Market is stable. Using tight spreads for frequent trades."
                }
            elif volatility_score < 0.5:
                # Medium volatility: Moderate spreads
                recommendations = {
                    "buy_percentage": 5.0,
                    "sell_percentage": 7.0,
                    "volatility_tier": "Medium",
                    "reason": "Moderate market activity. Using balanced spreads."
                }
            else:
                # High volatility: Wider spreads
                recommendations = {
                    "buy_percentage": 10.0,
                    "sell_percentage": 12.0,
                    "volatility_tier": "High",
                    "reason": "Market is volatile. Using wider spreads to avoid quick reversals."
                }

            # Add current settings context
            if settings:
                recommendations["current_buy_percentage"] = settings.get("buy_percentage", DEFAULT_BUY_PERCENTAGE)
                recommendations["current_sell_percentage"] = settings.get("sell_percentage", DEFAULT_SELL_PERCENTAGE)
                recommendations["current_reference_price"] = settings.get("reference_price", 0)

            return {
                "symbol": symbol.upper(),
                "recommendations": recommendations,
                "volatility_score": round(volatility_score, 2)
            }
        except Exception as e:
            logger.error(f"Recommendation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

    return router
