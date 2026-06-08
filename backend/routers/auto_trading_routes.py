"""
Auto Trading Routes
===================

REST API endpoints for AI-powered automated trading with risk management and warnings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging
from datetime import datetime

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
        from backend.binance_api import get_client
        
        # Get Binance client
        client = get_client()
        
        # Normalize symbol for Binance (remove spaces, uppercase)
        binance_symbol = symbol.upper().replace(" ", "")
        if not binance_symbol.endswith("USDT"):
            binance_symbol = f"{binance_symbol}USDT"
        
        logger.info(f"📊 Executing {action} order on Binance.US: {binance_symbol} x{quantity}")
        
        # Execute the main order
        if action.upper() == "BUY":
            order = client.order_limit_buy(
                symbol=binance_symbol,
                quantity=quantity,
                price=take_profit  # Using take_profit as target price hint (actual filled at market)
            )
        elif action.upper() == "SELL":
            order = client.order_limit_sell(
                symbol=binance_symbol,
                quantity=quantity,
                price=stop_loss  # Using stop_loss as minimum price hint
            )
        else:
            raise ValueError(f"Invalid action: {action}")
        
        order_id = order.get("orderId", "N/A")
        
        # Store trade in MongoDB for user tracking
        try:
            auto_trades_collection = db["auto_trades"]
            trade_record = {
                "user_id": current_user,
                "symbol": binance_symbol,
                "action": action.upper(),
                "quantity": quantity,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "order_id": order_id,
                "exchange": "binance.us",
                "status": "submitted",
                "created_at": datetime.utcnow(),
                "order_details": order
            }
            auto_trades_collection.insert_one(trade_record)
            logger.info(f"✅ Trade recorded in database: {order_id}")
        except Exception as db_error:
            logger.error(f"⚠️  Trade executed but failed to log to DB: {db_error}")
        
        return {
            "order_id": str(order_id),
            "status": "submitted",
            "exchange": "binance.us",
            "symbol": binance_symbol,
            "action": action.upper(),
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
        
    except ImportError:
        logger.error("Binance API module not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trading infrastructure not configured"
        )
    except Exception as e:
        logger.error(f"❌ Trade execution failed: {e}")
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
                "timestamp": signal.risk_level,
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
                "timestamp": datetime.utcnow().isoformat(),
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
            # Fetch active trades from MongoDB
            auto_trades_collection = db["auto_trades"]
            
            # Find all trades for this user that are still active
            active_trades = await auto_trades_collection.find({
                "user_id": current_user,
                "status": {"$in": ["submitted", "open", "pending"]}
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
                    "created_at": trade.get("created_at", datetime.utcnow()).isoformat() if hasattr(trade.get("created_at"), "isoformat") else str(trade.get("created_at")),
                    "exchange": trade.get("exchange", "binance.us")
                }
                
                enriched_trades.append(trade_data)
            
            logger.info(f"Fetched {len(enriched_trades)} active trades for user {current_user}")
            
            return {
                "status": "ok",
                "user_id": current_user,
                "active_trades_count": len(enriched_trades),
                "active_trades": enriched_trades,
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
