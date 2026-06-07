"""
Auto Trading Module for CryptoAI
=================================

Provides AI-driven automated trading decisions with extensive risk management
and warnings about the dangers of algorithmic trading.

⚠️ WARNING: Automated trading carries significant risks including:
- Flash crashes and market volatility exploitation
- Execution errors in volatile markets
- Unintended large position sizes
- Inability to react to breaking news
- Leverage amplification of losses
- Technical glitches causing runaway trades
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AutoTradeRisk(BaseModel):
    """Risk assessment for auto trading."""
    level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    score: float  # 0-100
    warnings: List[str]
    recommendation: str


class AutoTradeSignal(BaseModel):
    """AI-generated trading signal."""
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0-100
    target_price: float
    stop_loss: float
    take_profit: float
    position_size_pct: float  # % of portfolio
    reasoning: str
    risk_level: AutoTradeRisk


class AutoTradeRequest(BaseModel):
    """Request to execute auto trade."""
    symbol: str
    action: str
    quantity: float
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    acknowledgement_risks_understood: bool = False
    acknowledgement_terms_accepted: bool = False


class AIDangerousWarnings:
    """Collection of critical warnings about AI auto trading."""
    
    WARNINGS = [
        {
            "title": "🚨 CRITICAL: No Guarantee of Profit",
            "description": "AI trading models can fail catastrophically in unprecedented market conditions. Past performance does NOT guarantee future results.",
            "severity": "CRITICAL"
        },
        {
            "title": "💥 Flash Crash Risk",
            "description": "Automated trades can trigger or amplify flash crashes. Your positions may be liquidated at extreme prices in seconds.",
            "severity": "CRITICAL"
        },
        {
            "title": "⏱️ Execution Risk",
            "description": "Market orders execute instantly. You may get significantly worse prices than displayed, especially in volatile markets.",
            "severity": "HIGH"
        },
        {
            "title": "📉 Leverage Amplification",
            "description": "Using margin/leverage with auto trading amplifies both gains AND losses. You can lose more than your initial investment.",
            "severity": "CRITICAL"
        },
        {
            "title": "📰 News Blindness",
            "description": "AI cannot react to breaking news faster than humans. Your bot may hold losing positions during major announcements.",
            "severity": "HIGH"
        },
        {
            "title": "🐛 Technical Glitches",
            "description": "Software bugs can cause unintended trades, duplicate orders, or positions that spiral out of control in seconds.",
            "severity": "HIGH"
        },
        {
            "title": "🌊 Liquidity Evaporation",
            "description": "In low-liquidity markets (altcoins), your large automated orders can move prices drastically against you.",
            "severity": "HIGH"
        },
        {
            "title": "⚡ Speed Disadvantage",
            "description": "High-frequency traders have microsecond advantages. Retail AI bots are at a structural disadvantage.",
            "severity": "MEDIUM"
        },
        {
            "title": "🔗 Correlated Failures",
            "description": "During market stress, all assets crash together. Your diversification strategy won't protect you.",
            "severity": "HIGH"
        },
        {
            "title": "🎯 Backtest Trap",
            "description": "AI trained on historical data often overfit. Models that work on backtests fail spectacularly on new market regimes.",
            "severity": "HIGH"
        },
        {
            "title": "💻 System Overload",
            "description": "Exchange APIs go down, internet disconnects, or your computer crashes during critical moments.",
            "severity": "MEDIUM"
        },
        {
            "title": "📊 Data Quality Issues",
            "description": "Stale prices, missing data points, or exchange data corruption can lead to completely wrong trading decisions.",
            "severity": "HIGH"
        },
        {
            "title": "🔄 Slippage Accumulation",
            "description": "Small slippage on each trade compounds quickly. High-frequency auto trading can lose 5-20% of gains to slippage.",
            "severity": "MEDIUM"
        },
        {
            "title": "🎲 Black Swan Events",
            "description": "Crypto market is prone to 50%+ single-day crashes. Your stop losses may not execute, or execute at catastrophic prices.",
            "severity": "CRITICAL"
        },
        {
            "title": "👻 Phantom Liquidity",
            "description": "Large bid/ask walls disappear instantly. What looks liquid might evaporate when you try to sell.",
            "severity": "HIGH"
        }
    ]


async def assess_auto_trade_risk(
    symbol: str,
    action: str,
    quantity: float,
    current_price: float,
    portfolio_value: float,
    market_volatility: float = 0.05
) -> AutoTradeRisk:
    """
    Assess risk level for proposed auto trade.
    
    Args:
        symbol: Trading pair symbol
        action: BUY or SELL
        quantity: Number of units
        current_price: Current market price
        portfolio_value: Total portfolio value
        market_volatility: Current 30-day volatility
        
    Returns:
        Risk assessment with warnings and recommendations
    """
    warnings = []
    score = 0
    
    position_value = quantity * current_price
    position_pct = (position_value / portfolio_value) * 100 if portfolio_value > 0 else 0
    
    # Check position size
    if position_pct > 50:
        warnings.append(f"Position exceeds 50% of portfolio ({position_pct:.1f}%)")
        score += 30
    elif position_pct > 25:
        warnings.append(f"Position exceeds 25% of portfolio ({position_pct:.1f}%)")
        score += 20
    elif position_pct > 10:
        warnings.append(f"Position exceeds 10% of portfolio ({position_pct:.1f}%)")
        score += 10
    
    # Check market volatility
    if market_volatility > 0.10:
        warnings.append(f"High market volatility detected ({market_volatility*100:.1f}%)")
        score += 25
    elif market_volatility > 0.08:
        warnings.append(f"Elevated market volatility ({market_volatility*100:.1f}%)")
        score += 15
    
    # Determine risk level
    if score >= 70:
        level = "CRITICAL"
        recommendation = "STRONGLY RECOMMEND CANCELING THIS TRADE. Risk is too high for automated execution."
    elif score >= 50:
        level = "HIGH"
        recommendation = "Use extreme caution. Consider reducing position size or waiting for better market conditions."
    elif score >= 30:
        level = "MEDIUM"
        recommendation = "Proceed with caution. Use stop-loss and position size limits."
    else:
        level = "LOW"
        recommendation = "Risk profile appears acceptable. Still apply standard risk management."
    
    return AutoTradeRisk(
        level=level,
        score=score,
        warnings=warnings,
        recommendation=recommendation
    )


async def generate_ai_trading_signal(
    symbol: str,
    price_history: List[float],
    volume_history: List[float],
    sentiment_score: float = 0.5,
    technical_indicators: Dict = None
) -> AutoTradeSignal:
    """
    Generate AI trading signal with extensive disclaimers.
    
    ⚠️ This signal is for educational purposes only!
    
    Args:
        symbol: Trading pair
        price_history: Recent price data
        volume_history: Recent volume data
        sentiment_score: 0-1 sentiment (0=bearish, 1=bullish)
        technical_indicators: RSI, MACD, Bollinger Bands, etc.
        
    Returns:
        Trading signal with confidence level
    """
    
    technical_indicators = technical_indicators or {}
    
    # Simple trend analysis
    if len(price_history) < 2:
        return AutoTradeSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0,
            target_price=price_history[-1] if price_history else 0,
            stop_loss=0,
            take_profit=0,
            position_size_pct=0,
            reasoning="Insufficient data for analysis",
            risk_level=AutoTradeRisk(
                level="CRITICAL",
                score=100,
                warnings=["Not enough price data to generate signal"],
                recommendation="Do not trade"
            )
        )
    
    current_price = price_history[-1]
    prev_price = price_history[-2]
    price_change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price != 0 else 0
    
    # Determine action
    if sentiment_score > 0.65 and price_change_pct < 5:
        action = "BUY"
        confidence = min(85, (sentiment_score * 100))
        target_price = current_price * 1.05
        stop_loss = current_price * 0.97
    elif sentiment_score < 0.35 and price_change_pct > -5:
        action = "SELL"
        confidence = min(85, ((1 - sentiment_score) * 100))
        target_price = current_price * 0.95
        stop_loss = current_price * 1.03
    else:
        action = "HOLD"
        confidence = 50
        target_price = current_price
        stop_loss = current_price * 0.95
    
    take_profit = target_price * 1.02 if action == "BUY" else target_price * 0.98
    
    # Risk assessment
    risk = await assess_auto_trade_risk(
        symbol=symbol,
        action=action,
        quantity=1,
        current_price=current_price,
        portfolio_value=100000,  # Default portfolio size
        market_volatility=abs(price_change_pct) / 100
    )
    
    reasoning = f"Based on sentiment analysis (score: {sentiment_score:.2f}), "
    reasoning += f"recent price movement ({price_change_pct:+.2f}%), "
    reasoning += f"and technical indicators, AI recommends {action}. "
    reasoning += f"⚠️ Confidence: {confidence:.0f}% (Still NOT a guarantee)"
    
    return AutoTradeSignal(
        symbol=symbol,
        action=action,
        confidence=confidence,
        target_price=target_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size_pct=max(1, min(5, 100 / confidence * 2)),  # Scale position with confidence
        reasoning=reasoning,
        risk_level=risk
    )


def validate_auto_trade_request(request: AutoTradeRequest) -> tuple[bool, str]:
    """
    Validate auto trade request has proper acknowledgements.
    
    Args:
        request: Auto trade request
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not request.acknowledgement_risks_understood:
        return False, "You must acknowledge understanding the risks of automated trading"
    
    if not request.acknowledgement_terms_accepted:
        return False, "You must accept the auto trading terms and conditions"
    
    if request.action not in ["BUY", "SELL"]:
        return False, f"Invalid action: {request.action}"
    
    if request.quantity <= 0:
        return False, "Quantity must be positive"
    
    return True, ""


def get_all_warnings() -> List[Dict]:
    """Get all critical warnings about AI auto trading."""
    return AIDangerousWarnings.WARNINGS
