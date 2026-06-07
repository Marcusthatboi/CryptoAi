"""
Advanced AI Trading Signal Generator
====================================

Uses technical analysis to generate real trading signals:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)  
- Bollinger Bands
- Market momentum
- Volume analysis
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical analysis indicators"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        RSI = 100 - (100 / (1 + RS))
        where RS = avg_gain / avg_loss
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d for d in deltas if d > 0]
        losses = [abs(d) for d in deltas if d < 0]
        
        avg_gain = statistics.mean(gains[-period:]) if gains else 0
        avg_loss = statistics.mean(losses[-period:]) if losses else 0
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return max(0, min(100, rsi))
    
    @staticmethod
    def calculate_macd(prices: List[float]) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        Returns dict with: macd_line, signal_line, histogram
        """
        if len(prices) < 26:
            return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}
        
        # Calculate exponential moving averages
        ema_12 = TechnicalIndicators.calculate_ema(prices, 12)
        ema_26 = TechnicalIndicators.calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        signal_line = TechnicalIndicators.calculate_ema([macd_line], 9)
        histogram = macd_line - signal_line
        
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram
        }
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return statistics.mean(prices)
        
        k = 2 / (period + 1)
        ema = statistics.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price * k) + (ema * (1 - k))
        
        return ema
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        Returns dict with: upper, middle, lower
        """
        if len(prices) < period:
            return {"upper": 0.0, "middle": 0.0, "lower": 0.0}
        
        recent_prices = prices[-period:]
        middle = statistics.mean(recent_prices)
        stdev = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
        
        upper = middle + (stdev * std_dev)
        lower = middle - (stdev * std_dev)
        
        return {"upper": upper, "middle": middle, "lower": lower}
    
    @staticmethod
    def calculate_momentum(prices: List[float], period: int = 12) -> float:
        """Calculate price momentum (rate of change)"""
        if len(prices) < period + 1:
            return 0.0
        
        current = prices[-1]
        previous = prices[-(period + 1)]
        
        if previous == 0:
            return 0.0
        
        momentum_pct = ((current - previous) / previous) * 100
        return momentum_pct


class SignalGenerator:
    """Generate trading signals from market data"""
    
    @staticmethod
    def generate_signal(
        symbol: str,
        current_price: float,
        price_history: List[float],
        volume_data: Optional[List[float]] = None,
        market_sentiment: str = "neutral"
    ) -> Dict:
        """
        Generate trading signal with confidence score
        
        Returns:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": 0-100,
                "target_price": float,
                "stop_loss": float,
                "take_profit": float,
                "reasoning": str,
                "indicators": {...}
            }
        """
        
        if len(price_history) < 26:
            return SignalGenerator._neutral_signal(symbol, current_price, "Insufficient data")
        
        # Calculate technical indicators
        rsi = TechnicalIndicators.calculate_rsi(price_history)
        macd = TechnicalIndicators.calculate_macd(price_history)
        bb = TechnicalIndicators.calculate_bollinger_bands(price_history)
        momentum = TechnicalIndicators.calculate_momentum(price_history)
        
        # Score each indicator
        scores = []
        reasoning_parts = []
        
        # RSI Analysis (0-100, 30=oversold, 70=overbought)
        rsi_score = SignalGenerator._score_rsi(rsi)
        scores.append(rsi_score)
        if rsi < 30:
            reasoning_parts.append(f"RSI oversold at {rsi:.1f} (bullish)")
        elif rsi > 70:
            reasoning_parts.append(f"RSI overbought at {rsi:.1f} (bearish)")
        
        # MACD Analysis
        macd_score = SignalGenerator._score_macd(macd)
        scores.append(macd_score)
        if macd["histogram"] > 0:
            reasoning_parts.append("MACD bullish (positive histogram)")
        elif macd["histogram"] < 0:
            reasoning_parts.append("MACD bearish (negative histogram)")
        
        # Bollinger Bands Analysis
        bb_score = SignalGenerator._score_bollinger_bands(current_price, bb)
        scores.append(bb_score)
        if current_price < bb["lower"]:
            reasoning_parts.append("Price below lower Bollinger Band (oversold)")
        elif current_price > bb["upper"]:
            reasoning_parts.append("Price above upper Bollinger Band (overbought)")
        
        # Momentum Analysis
        momentum_score = SignalGenerator._score_momentum(momentum)
        scores.append(momentum_score)
        if momentum > 5:
            reasoning_parts.append(f"Strong upward momentum {momentum:.1f}%")
        elif momentum < -5:
            reasoning_parts.append(f"Strong downward momentum {momentum:.1f}%")
        
        # Market Sentiment
        sentiment_score = SignalGenerator._score_sentiment(market_sentiment)
        scores.append(sentiment_score)
        
        # Calculate average confidence
        avg_confidence = statistics.mean(scores)
        
        # Determine action
        if avg_confidence > 60:
            action = "BUY" if avg_confidence > 60 else "SELL"
            # For BUY signals
            if momentum > 0 and rsi < 70:
                action = "BUY"
                target_price = current_price * 1.05  # 5% target
                stop_loss = current_price * 0.97    # 3% stop loss
                take_profit = current_price * 1.10  # 10% take profit
                reasoning = f"Bullish indicators align. {' '.join(reasoning_parts)}"
            else:
                action = "SELL"
                target_price = current_price * 0.95
                stop_loss = current_price * 1.03
                take_profit = current_price * 0.90
                reasoning = f"Bearish indicators align. {' '.join(reasoning_parts)}"
        else:
            action = "HOLD"
            target_price = current_price
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05
            reasoning = "Mixed signals - HOLD for more clarity"
        
        return {
            "action": action,
            "confidence": min(100, max(0, avg_confidence)),
            "target_price": target_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "reasoning": reasoning,
            "indicators": {
                "rsi": rsi,
                "macd_line": macd["macd_line"],
                "signal_line": macd["signal_line"],
                "histogram": macd["histogram"],
                "momentum": momentum,
                "bollinger_upper": bb["upper"],
                "bollinger_middle": bb["middle"],
                "bollinger_lower": bb["lower"],
            }
        }
    
    @staticmethod
    def _score_rsi(rsi: float) -> float:
        """Score RSI on 0-100 scale"""
        if rsi < 30:
            return 75  # Oversold = bullish
        elif rsi > 70:
            return 25  # Overbought = bearish
        else:
            return 50  # Neutral
    
    @staticmethod
    def _score_macd(macd: Dict[str, float]) -> float:
        """Score MACD on 0-100 scale"""
        histogram = macd.get("histogram", 0)
        macd_line = macd.get("macd_line", 0)
        signal_line = macd.get("signal_line", 0)
        
        if histogram > 0 and macd_line > signal_line:
            return 75  # Bullish crossover
        elif histogram < 0 and macd_line < signal_line:
            return 25  # Bearish crossover
        else:
            return 50  # Neutral
    
    @staticmethod
    def _score_bollinger_bands(price: float, bb: Dict[str, float]) -> float:
        """Score Bollinger Bands on 0-100 scale"""
        upper = bb.get("upper", 0)
        lower = bb.get("lower", 0)
        
        if price < lower:
            return 75  # Oversold
        elif price > upper:
            return 25  # Overbought
        else:
            if upper != lower:
                position = (price - lower) / (upper - lower)
                return 50 + (position - 0.5) * 50
            else:
                return 50
    
    @staticmethod
    def _score_momentum(momentum: float) -> float:
        """Score momentum on 0-100 scale"""
        return min(100, max(0, 50 + momentum * 5))  # ±10% = extreme
    
    @staticmethod
    def _score_sentiment(sentiment: str) -> float:
        """Score market sentiment"""
        sentiment_map = {
            "very_bullish": 85,
            "bullish": 70,
            "neutral": 50,
            "bearish": 30,
            "very_bearish": 15
        }
        return sentiment_map.get(sentiment.lower(), 50)
    
    @staticmethod
    def _neutral_signal(symbol: str, price: float, reason: str) -> Dict:
        """Return neutral signal"""
        return {
            "action": "HOLD",
            "confidence": 0,
            "target_price": price,
            "stop_loss": price * 0.95,
            "take_profit": price * 1.05,
            "reasoning": f"Insufficient data: {reason}",
            "indicators": {}
        }
