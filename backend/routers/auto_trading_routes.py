"""
Auto Trading Routes
===================

REST API endpoints for AI-powered automated trading with risk management and warnings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timezone
from copy import deepcopy
from pydantic import BaseModel

from backend.auto_trading import (
    AutoTradeRequest,
    AutoTradeSignal,
    AutoTradeRisk,
    generate_ai_trading_signal,
    assess_auto_trade_risk,
    validate_auto_trade_request,
    get_all_warnings,
)
from backend.db import get_db
from backend.subscription import get_user_subscription

logger = logging.getLogger(__name__)


ACTIVE_TRADE_STATUSES = {"submitted", "open", "pending"}
ACTIVE_TRADE_VISIBLE_STATUSES = {"submitted", "open", "pending", "close_submitted"}
TERMINAL_EXCHANGE_STATUSES = {"FILLED", "CANCELED", "REJECTED", "EXPIRED", "EXPIRED_IN_MATCH"}

RECONCILIATION_RUNTIME_METRICS: Dict[str, Any] = {
    "total_runs": 0,
    "successful_runs": 0,
    "failed_runs": 0,
    "consecutive_failure_runs": 0,
    "total_users_checked": 0,
    "total_users_failed": 0,
    "total_trades_checked": 0,
    "total_trades_updated": 0,
    "total_trade_failures": 0,
    "last_run_at": None,
    "last_success_at": None,
    "last_failure_at": None,
    "last_duration_seconds": None,
    "last_result": None,
    "last_error": None,
    "last_stale_summary": None,
}


def normalize_binance_symbol(raw_symbol: str) -> str:
    """Normalize user symbol input into Binance-US style symbols (e.g. BTCUSDT)."""
    normalized = str(raw_symbol or "").upper().strip()
    if not normalized:
        raise ValueError("Symbol is required")

    normalized = normalized.replace(" ", "").replace("-", "").replace("_", "").replace("/", "")

    if normalized.endswith("USDT"):
        return normalized
    if normalized.endswith("USD"):
        base = normalized[:-3]
        if not base:
            raise ValueError("Invalid symbol")
        return f"{base}USDT"

    return f"{normalized}USDT"


class AdjustStopsRequest(BaseModel):
    stop_loss: float
    take_profit: float


def validate_stop_take_profit(
    action: str,
    stop_loss: float,
    take_profit: float,
    current_price: float,
    *,
    min_distance_ratio: float = 0.001,
) -> Optional[str]:
    """Validate stop-loss/take-profit placement relative to current market price."""
    if stop_loss <= 0 or take_profit <= 0:
        return "stop_loss and take_profit must be greater than 0"
    if current_price <= 0:
        return "Unable to validate stops because current market price is unavailable"

    normalized_action = str(action or "").upper()
    if normalized_action not in {"BUY", "SELL"}:
        return "Action must be BUY or SELL"

    min_distance = current_price * min_distance_ratio

    if normalized_action == "BUY":
        if not stop_loss < current_price:
            return "For BUY trades, stop_loss must be below the current market price"
        if not take_profit > current_price:
            return "For BUY trades, take_profit must be above the current market price"
        if (current_price - stop_loss) < min_distance:
            return "stop_loss is too close to market price"
        if (take_profit - current_price) < min_distance:
            return "take_profit is too close to market price"
    else:
        if not stop_loss > current_price:
            return "For SELL trades, stop_loss must be above the current market price"
        if not take_profit < current_price:
            return "For SELL trades, take_profit must be below the current market price"
        if (stop_loss - current_price) < min_distance:
            return "stop_loss is too close to market price"
        if (current_price - take_profit) < min_distance:
            return "take_profit is too close to market price"

    return None


def get_current_market_price(symbol: str) -> float:
    """Fetch current market price for a symbol from Binance ticker endpoint."""
    from backend.binance_api import get_ticker

    normalized_symbol = normalize_binance_symbol(symbol)
    ticker = get_ticker(normalized_symbol)
    return float((ticker or {}).get("price") or 0)


def place_market_order_with_retry(
    *,
    symbol: str,
    side: str,
    quantity: float,
    max_attempts: int = 3,
) -> Tuple[Dict[str, Any], int]:
    """Place a market order with bounded retries for transient exchange failures."""
    from backend.binance_api import place_order as place_binance_order

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            order = place_binance_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
            )
            return order, attempt
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Market order attempt %s/%s failed for %s %s x%s: %s",
                attempt,
                max_attempts,
                side,
                symbol,
                quantity,
                exc,
            )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Exchange order failed after {max_attempts} attempts: {last_error}",
    )


def _to_utc_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def get_reconciliation_metrics_snapshot() -> Dict[str, Any]:
    return deepcopy(RECONCILIATION_RUNTIME_METRICS)


def record_reconciliation_run(
    *,
    result: Optional[Dict[str, Any]] = None,
    duration_seconds: Optional[float] = None,
    stale_summary: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    RECONCILIATION_RUNTIME_METRICS["total_runs"] += 1
    RECONCILIATION_RUNTIME_METRICS["last_run_at"] = now_iso
    RECONCILIATION_RUNTIME_METRICS["last_duration_seconds"] = duration_seconds

    if error:
        RECONCILIATION_RUNTIME_METRICS["failed_runs"] += 1
        RECONCILIATION_RUNTIME_METRICS["consecutive_failure_runs"] += 1
        RECONCILIATION_RUNTIME_METRICS["last_failure_at"] = now_iso
        RECONCILIATION_RUNTIME_METRICS["last_error"] = str(error)
        if stale_summary is not None:
            RECONCILIATION_RUNTIME_METRICS["last_stale_summary"] = stale_summary
        return

    RECONCILIATION_RUNTIME_METRICS["successful_runs"] += 1
    RECONCILIATION_RUNTIME_METRICS["consecutive_failure_runs"] = 0
    RECONCILIATION_RUNTIME_METRICS["last_success_at"] = now_iso
    RECONCILIATION_RUNTIME_METRICS["last_error"] = None

    if result is None:
        result = {}

    users_checked = int(result.get("users_checked", 0))
    users_failed = int(result.get("users_failed", 0))
    trades_checked = int(result.get("checked", 0))
    trades_updated = int(result.get("updated", 0))
    trade_failures = int(result.get("failed", 0))

    RECONCILIATION_RUNTIME_METRICS["total_users_checked"] += users_checked
    RECONCILIATION_RUNTIME_METRICS["total_users_failed"] += users_failed
    RECONCILIATION_RUNTIME_METRICS["total_trades_checked"] += trades_checked
    RECONCILIATION_RUNTIME_METRICS["total_trades_updated"] += trades_updated
    RECONCILIATION_RUNTIME_METRICS["total_trade_failures"] += trade_failures
    RECONCILIATION_RUNTIME_METRICS["last_result"] = result
    RECONCILIATION_RUNTIME_METRICS["last_stale_summary"] = stale_summary


async def detect_stale_trade_states(
    db,
    *,
    stale_seconds: int = 900,
    max_records: int = 2000,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan tracked trade states and report stale lifecycle records."""
    auto_trades_collection = db["auto_trades"]
    query: Dict[str, Any] = {"status": {"$in": ["submitted", "close_submitted"]}}
    if user_id:
        query["user_id"] = user_id

    tracked = await auto_trades_collection.find(query).sort("created_at", -1).to_list(length=max_records)
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc.timestamp() - float(stale_seconds)

    stale_count = 0
    by_status: Dict[str, int] = {"submitted": 0, "close_submitted": 0}
    oldest_age_seconds = 0.0

    for trade in tracked:
        status_value = str(trade.get("status") or "").lower()
        reference_time = _to_utc_datetime(trade.get("updated_at")) or _to_utc_datetime(trade.get("created_at"))
        if not reference_time:
            continue

        age_seconds = now_utc.timestamp() - reference_time.timestamp()
        if reference_time.timestamp() <= cutoff:
            stale_count += 1
            if status_value in by_status:
                by_status[status_value] += 1
            oldest_age_seconds = max(oldest_age_seconds, age_seconds)

    return {
        "scanned": len(tracked),
        "stale_count": stale_count,
        "stale_seconds_threshold": int(stale_seconds),
        "oldest_age_seconds": int(oldest_age_seconds),
        "by_status": by_status,
    }


async def reconcile_user_trade_statuses(current_user: str, db, *, max_trades: int = 100) -> Dict[str, int]:
    """Reconcile user trades with exchange order status and update lifecycle state."""
    from backend.binance_api import get_order_status

    auto_trades_collection = db["auto_trades"]
    tracked_statuses = ["submitted", "open", "pending", "close_submitted"]
    tracked_trades = await auto_trades_collection.find(
        {
            "user_id": current_user,
            "status": {"$in": tracked_statuses},
        }
    ).sort("created_at", -1).to_list(length=max_trades)

    checked = 0
    updated = 0
    failures = 0

    for trade in tracked_trades:
        checked += 1
        lifecycle_status = str(trade.get("status") or "").lower()
        symbol = normalize_binance_symbol(trade.get("symbol", ""))
        exchange_order_id = trade.get("close_order_id") if lifecycle_status == "close_submitted" else trade.get("order_id")
        if exchange_order_id in (None, "", "N/A"):
            continue

        try:
            parsed_order_id = int(str(exchange_order_id))
            exchange_order = get_order_status(symbol, parsed_order_id)
            exchange_status = str((exchange_order or {}).get("status") or "").upper()
            if not exchange_status:
                continue

            now_iso = datetime.now(timezone.utc).isoformat()
            set_fields = {
                "updated_at": now_iso,
                "last_reconciled_at": now_iso,
            }
            if lifecycle_status == "close_submitted":
                set_fields["close_order_status"] = exchange_status
                if exchange_status == "FILLED":
                    set_fields["status"] = "closed"
                    set_fields["closed_at"] = now_iso
                elif exchange_status in (TERMINAL_EXCHANGE_STATUSES - {"FILLED"}):
                    set_fields["status"] = "close_failed"
            else:
                set_fields["exchange_order_status"] = exchange_status
                if exchange_status == "FILLED":
                    set_fields["status"] = "open"
                elif exchange_status in (TERMINAL_EXCHANGE_STATUSES - {"FILLED"}):
                    set_fields["status"] = "failed"

            await auto_trades_collection.update_one({"_id": trade.get("_id")}, {"$set": set_fields})
            updated += 1
        except Exception as exc:
            failures += 1
            logger.warning("Failed to reconcile order %s for user %s: %s", exchange_order_id, current_user, exc)

    return {
        "checked": checked,
        "updated": updated,
        "failed": failures,
    }


async def reconcile_all_active_trade_statuses(
    db,
    *,
    max_users: int = 200,
    max_trades_per_user: int = 100,
) -> Dict[str, int]:
    """Reconcile active trade lifecycle states across all users with active/closing trades."""
    auto_trades_collection = db["auto_trades"]
    tracked_statuses = list(ACTIVE_TRADE_VISIBLE_STATUSES)
    user_ids = await auto_trades_collection.distinct(
        "user_id",
        {"status": {"$in": tracked_statuses}},
    )

    summary = {
        "users_checked": 0,
        "users_failed": 0,
        "checked": 0,
        "updated": 0,
        "failed": 0,
    }

    for user_id in (user_ids or [])[:max_users]:
        try:
            result = await reconcile_user_trade_statuses(
                str(user_id),
                db,
                max_trades=max_trades_per_user,
            )
            summary["users_checked"] += 1
            summary["checked"] += int(result.get("checked", 0))
            summary["updated"] += int(result.get("updated", 0))
            summary["failed"] += int(result.get("failed", 0))
        except Exception as exc:
            summary["users_failed"] += 1
            logger.warning("Failed to reconcile user %s active trades: %s", user_id, exc)

    return summary


async def verify_premium_subscription(current_user: str, db) -> str:
    """
    Dependency to verify user has premium subscription.
    
    Auto trading is a premium-only feature.
    
    Args:
        current_user: Authenticated user ID
        db: Database connection
        
    Returns:
        current_user if premium
        
    Raises:
        HTTPException 403 if not premium
    """
    try:
        subscription = await get_user_subscription(db, current_user)
        
        # If no subscription, user is on free tier
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auto Trading is a Premium feature. Please upgrade your subscription to access this feature.",
                headers={"X-Feature": "premium-required", "X-Redirect-To": "/pricing"}
            )
        
        # Check tier
        tier = subscription.get("tier", "free").lower()
        if tier != "premium":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auto Trading is a Premium feature. Your current tier is '{}'. Please upgrade to Premium.".format(tier),
                headers={"X-Feature": "premium-required", "X-Redirect-To": "/pricing"}
            )
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying premium subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying subscription"
        )


async def execute_trade_on_exchange(
    symbol: str,
    action: str,
    quantity: float,
    stop_loss: float,
    take_profit: float,
    current_user: str,
    db
) -> Dict[str, Any]:
    """
    Execute an actual trade on Binance.US (or other exchanges).
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        action: "BUY" or "SELL"
        quantity: Order quantity
        stop_loss: Stop loss price
        take_profit: Take profit price
        current_user: User placing the trade
        db: Database connection
        
    Returns:
        Trade execution details with order_id and status
    """
    try:
        binance_symbol = normalize_binance_symbol(symbol)
        normalized_action = str(action or "").upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be BUY or SELL",
            )

        current_price = get_current_market_price(binance_symbol)
        validation_error = validate_stop_take_profit(
            normalized_action,
            float(stop_loss),
            float(take_profit),
            current_price,
        )
        if validation_error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation_error)

        logger.info(
            "Executing %s order on Binance.US: %s x%s",
            normalized_action,
            binance_symbol,
            quantity,
        )

        order, attempt_count = place_market_order_with_retry(
            symbol=binance_symbol,
            side=normalized_action,
            quantity=float(quantity),
        )

        order_id = str(order.get("order_id", "N/A"))
        now = datetime.now(timezone.utc)
        trade_record = {
            "user_id": current_user,
            "order_id": order_id,
            "symbol": binance_symbol,
            "action": normalized_action,
            "quantity": float(quantity),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "exchange": "binance.us",
            "status": "submitted",
            "created_at": now,
            "updated_at": now,
            "submitted_price": current_price,
            "order_attempt_count": attempt_count,
            "order_details": order,
        }

        auto_trades_collection = db["auto_trades"]
        await auto_trades_collection.insert_one(trade_record)
        logger.info("Trade recorded in database: %s", order_id)

        return {
            "order_id": order_id,
            "status": "submitted",
            "exchange": "binance.us",
            "symbol": binance_symbol,
            "action": normalized_action,
            "quantity": float(quantity),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "market_price": current_price,
            "order_attempt_count": attempt_count,
        }

    except ImportError:
        logger.error("Binance API module not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trading infrastructure not configured"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade execution failed: {str(e)}"
        )


def create_auto_trading_router(get_current_user_dependency, get_db_fn=get_db):
    """Create auto trading router with proper dependencies."""
    
    router = APIRouter(prefix="/api/auto-trading", tags=["auto-trading"])
    
    @router.get("/warnings")
    async def get_auto_trading_warnings():
        """
        Get all critical warnings about AI auto trading.
        
        Returns a comprehensive list of dangers and risks that users
        MUST understand before enabling automated trading.
        
        🚨 THIS ENDPOINT IS CRITICAL FOR RISK DISCLOSURE 🚨
        """
        warnings = get_all_warnings()
        
        return {
            "status": "ok",
            "total_warnings": len(warnings),
            "severity_breakdown": {
                "CRITICAL": len([w for w in warnings if w["severity"] == "CRITICAL"]),
                "HIGH": len([w for w in warnings if w["severity"] == "HIGH"]),
                "MEDIUM": len([w for w in warnings if w["severity"] == "MEDIUM"]),
            },
            "warnings": warnings,
            "disclaimer": (
                "⚠️ AUTOMATED TRADING DISCLAIMER ⚠️\n\n"
                "AI-powered automated trading is EXTREMELY DANGEROUS and can result in:\n"
                "• Complete loss of capital\n"
                "• Losses exceeding initial investment (if using leverage)\n"
                "• Trades executing at catastrophic prices in volatile markets\n"
                "• Technical glitches causing unintended trades\n"
                "• Inability to react to breaking news or market events\n\n"
                "DO NOT enable auto trading unless you:\n"
                "1. Fully understand cryptocurrency market risks\n"
                "2. Can afford to lose 100% of the trading capital\n"
                "3. Have read and understood all warnings above\n"
                "4. Use only small position sizes (max 5% of portfolio per trade)\n"
                "5. Set tight stop-losses on all positions\n"
                "6. Monitor your account actively\n\n"
                "By using auto trading, you accept ALL risks and losses."
            )
        }
    
    @router.post("/analyze/{symbol}")
    async def analyze_symbol_for_auto_trading(
        symbol: str,
        price_history: List[float],
        volume_history: List[float],
        sentiment_score: float = 0.5,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        Analyze a symbol and generate AI trading signal.
        
        ⚠️ PREMIUM FEATURE - Requires Premium subscription
        ⚠️ FOR ANALYSIS PURPOSES ONLY - NOT A TRADING RECOMMENDATION
        
        Args:
            symbol: Trading pair (e.g., BTC/USD)
            price_history: Recent price data
            volume_history: Recent volume data
            sentiment_score: 0-1 sentiment (0=bearish, 1=bullish)
            current_user: Authenticated user
            
        Returns:
            AI-generated trading signal with confidence levels and risks
        """
        # Verify premium subscription
        await verify_premium_subscription(current_user, db)
        
        try:
            logger.info(f"Analyzing {symbol} for auto trading (user: {current_user})")
            
            signal = await generate_ai_trading_signal(
                symbol=symbol,
                price_history=price_history,
                volume_history=volume_history,
                sentiment_score=sentiment_score
            )
            
            return {
                "status": "ok",
                "symbol": symbol,
                "signal": signal.dict(),
                "disclaimer": "⚠️ This signal is for EDUCATIONAL PURPOSES ONLY and should NOT be used as investment advice",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing symbol: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error analyzing symbol: {str(e)}"
            )
    
    @router.post("/assess-risk")
    async def assess_trade_risk(
        symbol: str,
        action: str,
        quantity: float,
        current_price: float,
        portfolio_value: float,
        market_volatility: float = 0.05,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        Assess risk profile of a proposed auto trade.
        
        ⚠️ PREMIUM FEATURE - Requires Premium subscription
        
        Args:
            symbol: Trading pair
            action: BUY or SELL
            quantity: Order size
            current_price: Current market price
            portfolio_value: Total portfolio value
            market_volatility: Current volatility estimate (0-1)
            current_user: Authenticated user
            
        Returns:
            Risk assessment with warnings and recommendations
        """
        # Verify premium subscription
        await verify_premium_subscription(current_user, db)
        
        try:
            risk = await assess_auto_trade_risk(
                symbol=symbol,
                action=action,
                quantity=quantity,
                current_price=current_price,
                portfolio_value=portfolio_value,
                market_volatility=market_volatility
            )
            
            return {
                "status": "ok",
                "risk_assessment": risk.dict(),
                "position_size_pct": (quantity * current_price / portfolio_value * 100) if portfolio_value > 0 else 0
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error assessing trade risk: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error assessing trade risk: {str(e)}"
            )
    
    @router.post("/preview")
    async def preview_auto_trade(
        request: AutoTradeRequest,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        Preview an auto trade WITHOUT executing it.
        
        ⚠️ PREMIUM FEATURE - Requires Premium subscription
        
        This endpoint validates the trade request and shows what would happen,
        but does NOT actually execute any transactions.
        
        Args:
            request: Auto trade request details
            current_user: Authenticated user
            
        Returns:
            Trade preview with risk assessment
        """
        # Verify premium subscription
        await verify_premium_subscription(current_user, db)
        
        try:
            # Validate acknowledgements
            is_valid, error_msg = validate_auto_trade_request(request)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            logger.info(f"Previewing auto trade for {request.symbol} (user: {current_user})")
            
            return {
                "status": "preview",
                "symbol": request.symbol,
                "action": request.action,
                "quantity": request.quantity,
                "stop_loss": request.stop_loss,
                "take_profit": request.take_profit,
                "max_estimated_loss": (request.quantity * request.stop_loss * 1.02) if request.stop_loss else "Not set",
                "max_estimated_gain": (request.quantity * request.take_profit * 0.98) if request.take_profit else "Not set",
                "warnings": [
                    "This is a PREVIEW ONLY",
                    "Actual execution prices may vary significantly",
                    "Market conditions can change rapidly",
                    "Slippage may occur on execution"
                ],
                "message": "Click 'Confirm Auto Trade' to execute this trade. You will be prompted again to confirm before any funds are committed."
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error previewing auto trade: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error previewing auto trade: {str(e)}"
            )
    
    @router.post("/execute")
    async def execute_auto_trade(
        request: AutoTradeRequest,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        EXECUTE an automated trade with AI recommendations.
        
        🚨 THIS ENDPOINT COMMITS REAL FUNDS - PREMIUM FEATURE 🚨
        
        Requires Premium subscription.
        
        This endpoint:
        1. Validates all risk acknowledgements
        2. Checks position size limits
        3. Verifies stop-loss and take-profit settings
        4. Executes the trade
        5. Records trade in user portfolio
        
        IMPORTANT: The user MUST have:
        - Acknowledged all risks
        - Accepted auto trading terms
        - Confirmed they understand potential total loss
        
        Args:
            request: Auto trade request (with acknowledgements)
            current_user: Authenticated user
            
        Returns:
            Trade execution result
        """
        # Verify premium subscription
        await verify_premium_subscription(current_user, db)
        
        try:
            # Double-check acknowledgements
            is_valid, error_msg = validate_auto_trade_request(request)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            logger.warning(f"⚠️  AUTO TRADE EXECUTION - User: {current_user}, Symbol: {request.symbol}, Action: {request.action}, Qty: {request.quantity}")
            
            # Safety checks
            if request.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0"
                )
            
            if not request.stop_loss:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stop-loss is REQUIRED for auto trading"
                )
            
            if not request.take_profit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Take-profit is REQUIRED for auto trading"
                )
            
            # Execute trade on Binance or Alpaca based on request
            trade_result = await execute_trade_on_exchange(
                symbol=request.symbol,
                action=request.action,
                quantity=request.quantity,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit,
                current_user=current_user,
                db=db
            )
            
            logger.info(f"✅ Auto trade executed: {request.symbol} {request.action} x{request.quantity}")
            
            return {
                "status": "executed",
                "symbol": request.symbol,
                "action": request.action,
                "quantity": request.quantity,
                "stop_loss": request.stop_loss,
                "take_profit": request.take_profit,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "order_id": trade_result.get("order_id", "N/A"),
                "exchange": trade_result.get("exchange", "binance"),
                "message": "⚠️  Trade has been submitted. Monitor your position actively and be prepared to take manual action if needed.",
                "important_reminders": [
                    "Check your position regularly",
                    "Be prepared for price gaps that skip your stop-loss",
                    "Remember slippage may cause worse execution prices",
                    "Market can move dramatically overnight"
                ]
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing auto trade: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing auto trade: {str(e)}"
            )
    
    @router.get("/user/active-trades")
    async def get_user_active_auto_trades(
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        Get all active auto trades for the current user.
        
        ⚠️ PREMIUM FEATURE - Requires Premium subscription
        
        Returns:
            List of active trades with real-time status, P&L, and controls
        """
        # Verify premium subscription
        await verify_premium_subscription(current_user, db)
        
        try:
            reconciliation = await reconcile_user_trade_statuses(current_user, db)

            # Fetch active trades from MongoDB
            auto_trades_collection = db["auto_trades"]
            
            # Find all trades for this user that are still active
            active_trades = await auto_trades_collection.find({
                "user_id": current_user,
                "status": {"$in": list(ACTIVE_TRADE_VISIBLE_STATUSES)}
            }).sort("created_at", -1).to_list(length=None)
            
            # Enrich trades with current price info
            enriched_trades = []
            for trade in active_trades:
                trade_data = {
                    "order_id": str(trade.get("order_id", "N/A")),
                    "symbol": trade.get("symbol", "UNKNOWN"),
                    "action": trade.get("action", "BUY"),
                    "quantity": trade.get("quantity", 0),
                    "stop_loss": trade.get("stop_loss"),
                    "take_profit": trade.get("take_profit"),
                    "status": trade.get("status", "unknown"),
                    "created_at": trade.get("created_at", datetime.now(timezone.utc)).isoformat() if hasattr(trade.get("created_at"), "isoformat") else str(trade.get("created_at")),
                    "exchange": trade.get("exchange", "binance.us")
                }
                
                enriched_trades.append(trade_data)
            
            logger.info(f"Fetched {len(enriched_trades)} active trades for user {current_user}")
            
            return {
                "status": "ok",
                "user_id": current_user,
                "active_trades_count": len(enriched_trades),
                "active_trades": enriched_trades,
                "reconciliation": reconciliation,
                "message": f"You have {len(enriched_trades)} active auto trades" if enriched_trades else "No active auto trades currently running",
                "note": "P&L values are estimates. Check your exchange account for exact values."
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching active trades: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching active trades: {str(e)}"
            )

    @router.post("/trades/reconcile")
    async def reconcile_active_trades(
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """Force a reconciliation pass for active/closing trade lifecycle states."""
        await verify_premium_subscription(current_user, db)

        try:
            result = await reconcile_user_trade_statuses(current_user, db)
            return {
                "status": "ok",
                "message": "Trade statuses reconciled",
                "result": result,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reconciling active trades: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reconcile trades: {str(e)}"
            )

    @router.get("/trades/reconciliation/metrics")
    async def get_trade_reconciliation_metrics(
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """Return reconciliation runtime metrics and user stale-state summary."""
        await verify_premium_subscription(current_user, db)

        try:
            metrics = get_reconciliation_metrics_snapshot()
            user_stale = await detect_stale_trade_states(
                db,
                stale_seconds=900,
                max_records=500,
                user_id=current_user,
            )
            return {
                "status": "ok",
                "metrics": metrics,
                "user_stale_summary": user_stale,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching reconciliation metrics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch reconciliation metrics: {str(e)}"
            )

    @router.post("/trades/{order_id}/close")
    async def close_active_auto_trade(
        order_id: str,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """Close an active auto-trade by submitting a market order in the opposite direction."""
        await verify_premium_subscription(current_user, db)

        try:
            auto_trades_collection = db["auto_trades"]
            existing_trade = await auto_trades_collection.find_one({
                "user_id": current_user,
                "order_id": str(order_id),
            })

            if not existing_trade:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active trade not found")

            trade_status = str(existing_trade.get("status", "")).lower()
            if trade_status not in ACTIVE_TRADE_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Trade is not active (status: {trade_status or 'unknown'})"
                )

            original_action = str(existing_trade.get("action", "BUY")).upper()
            close_action = "SELL" if original_action == "BUY" else "BUY"
            quantity = float(existing_trade.get("quantity") or 0)
            if quantity <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trade quantity")

            symbol = normalize_binance_symbol(existing_trade.get("symbol", ""))
            close_order, attempt_count = place_market_order_with_retry(
                symbol=symbol,
                side=close_action,
                quantity=quantity,
            )

            close_status = str(close_order.get("status") or "submitted").upper()
            close_state = "closed" if close_status == "FILLED" else "close_submitted"
            close_message = "Trade closed successfully" if close_status == "FILLED" else "Close order submitted; awaiting full fill"

            now_iso = datetime.now(timezone.utc).isoformat()
            await auto_trades_collection.update_one(
                {"_id": existing_trade.get("_id")},
                {
                    "$set": {
                        "status": close_state,
                        "closed_at": now_iso if close_state == "closed" else None,
                        "close_reason": "manual_user_close",
                        "close_order_id": str(close_order.get("order_id")),
                        "close_order_status": close_status,
                        "close_attempt_count": attempt_count,
                        "close_order_details": close_order,
                        "updated_at": now_iso,
                    }
                }
            )

            return {
                "status": "success",
                "message": close_message,
                "order_id": str(order_id),
                "close_order_id": str(close_order.get("order_id")),
                "symbol": symbol,
                "action": close_action,
                "quantity": quantity,
                "close_order_status": close_status,
                "close_attempt_count": attempt_count,
                "closed_at": now_iso,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error closing active trade {order_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to close trade: {str(e)}"
            )

    @router.patch("/trades/{order_id}/stops")
    async def adjust_active_trade_stops(
        order_id: str,
        payload: AdjustStopsRequest,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """Adjust stop-loss and take-profit values for an active tracked trade."""
        await verify_premium_subscription(current_user, db)

        try:
            stop_loss = float(payload.stop_loss)
            take_profit = float(payload.take_profit)
            if stop_loss <= 0 or take_profit <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="stop_loss and take_profit must be greater than 0"
                )

            auto_trades_collection = db["auto_trades"]
            existing_trade = await auto_trades_collection.find_one({
                "user_id": current_user,
                "order_id": str(order_id),
            })

            if not existing_trade:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active trade not found")

            trade_status = str(existing_trade.get("status", "")).lower()
            if trade_status not in ACTIVE_TRADE_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Trade is not active (status: {trade_status or 'unknown'})"
                )

            action = str(existing_trade.get("action", "BUY")).upper()
            symbol = normalize_binance_symbol(existing_trade.get("symbol", ""))
            current_price = get_current_market_price(symbol)
            validation_error = validate_stop_take_profit(
                action,
                stop_loss,
                take_profit,
                current_price,
            )
            if validation_error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation_error)

            now_iso = datetime.now(timezone.utc).isoformat()
            await auto_trades_collection.update_one(
                {"_id": existing_trade.get("_id")},
                {
                    "$set": {
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "updated_at": now_iso,
                    },
                    "$push": {
                        "adjustments": {
                            "timestamp": now_iso,
                            "type": "stops",
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                        }
                    }
                }
            )

            return {
                "status": "success",
                "message": "Trade stops updated",
                "order_id": str(order_id),
                "symbol": symbol,
                "action": action,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "market_price": current_price,
                "updated_at": now_iso,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adjusting stops for trade {order_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to adjust stops: {str(e)}"
            )
    
    @router.post("/generate-signal/{symbol}")
    async def generate_trading_signal(
        symbol: str,
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        Generate real AI trading signal based on technical analysis.
        
        Uses multiple indicators:
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - Bollinger Bands
        - Market Momentum
        
        Returns trading signal with confidence score.
        """
        await verify_premium_subscription(current_user, db)
        
        try:
            from backend.signal_generator import SignalGenerator
            from backend.data_service import fetch_crypto_prices
            
            # Normalize symbol
            crypto_symbol = symbol.upper().replace("USDT", "").replace("USD", "")
            
            # Fetch price history
            price_data = await fetch_crypto_prices(crypto_symbol, limit=100)
            
            if not price_data or len(price_data) < 26:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient data for {symbol}. Need 26+ candles."
                )
            
            # Extract prices
            prices = [float(p.get("price", 0)) for p in price_data]
            current_price = prices[-1]
            
            # Generate signal
            signal = SignalGenerator.generate_signal(
                symbol=symbol,
                current_price=current_price,
                price_history=prices
            )
            
            logger.info(f"✅ Generated signal for {symbol}: {signal['action']} (confidence: {signal['confidence']:.1f}%)")
            
            return {
                "status": "success",
                "symbol": symbol,
                "signal": signal
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating signal: {str(e)}"
            )
    
    @router.post("/backtest")
    async def run_backtest(
        request: Dict[str, Any],
        current_user: str = Depends(get_current_user_dependency),
        db = Depends(get_db_fn)
    ):
        """
        Run backtest on historical data for strategy validation.
        
        Request body:
        {
            "symbol": "BTC",
            "period_days": 90,
            "initial_capital": 10000,
            "trade_size_pct": 0.1,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10
        }
        """
        await verify_premium_subscription(current_user, db)
        
        try:
            from backend.backtest_engine import BacktestEngine
            from backend.signal_generator import SignalGenerator
            
            symbol = request.get("symbol", "BTC")
            period_days = request.get("period_days", 90)
            initial_capital = request.get("initial_capital", 10000)
            trade_size_pct = request.get("trade_size_pct", 0.1)
            stop_loss_pct = request.get("stop_loss_pct", 0.05)
            take_profit_pct = request.get("take_profit_pct", 0.10)
            
            logger.info(f"🔄 Starting backtest for {symbol} ({period_days} days)")
            
            # Fetch historical data
            from backend.data_service import fetch_crypto_prices
            price_history = await fetch_crypto_prices(symbol, limit=period_days)
            
            if len(price_history) < 26:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient historical data for backtest"
                )
            
            # Format price data
            formatted_prices = []
            for p in price_history:
                formatted_prices.append({
                    "date": datetime.now(),  # Use current date for demo
                    "price": float(p.get("price", 0)),
                    "volume": float(p.get("volume", 0))
                })
            
            # Define strategy function
            def strategy_func(prices_so_far):
                if len(prices_so_far) < 26:
                    return "HOLD"
                recent_prices = [float(p["price"]) for p in prices_so_far[-100:]]
                signal = SignalGenerator.generate_signal(symbol, recent_prices[-1], recent_prices)
                return signal["action"]
            
            # Run backtest
            engine = BacktestEngine(initial_capital)
            results = engine.run_backtest(
                symbol=symbol,
                price_history=formatted_prices,
                strategy_func=strategy_func,
                trade_size_pct=trade_size_pct,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            
            return {
                "status": "success",
                "backtest_results": results
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error running backtest: {str(e)}"
            )
    
    return router
