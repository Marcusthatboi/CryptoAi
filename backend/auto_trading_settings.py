"""
Auto Trading Settings Management
Handles per-cryptocurrency auto trading configuration and monitoring
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AutoTradeActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"
    CONFIG_UPDATE = "CONFIG_UPDATE"


@dataclass
class AutoTradeAction:
    """Record of an automated trading action"""
    timestamp: str
    action_type: str  # BUY, SELL, ENABLE, DISABLE, CONFIG_UPDATE
    symbol: str
    price: float
    quantity: Optional[float] = None
    reason: str = ""
    profit_loss: float = 0.0


@dataclass
class CryptoAutoTradingSettings:
    """Per-cryptocurrency auto trading configuration"""
    user_id: str
    symbol: str
    enabled: bool = False
    buy_percentage: float = 5.0  # Drop % to trigger buy
    sell_percentage: float = 10.0  # Gain % to trigger sell
    reference_price: Optional[float] = None  # Starting price
    average_cost: Optional[float] = None  # Average purchase price
    total_quantity_held: float = 0.0
    last_action: Optional[Dict] = None
    actions_history: List[Dict] = None
    total_profit_loss: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "symbol": self.symbol,
            "enabled": self.enabled,
            "buy_percentage": self.buy_percentage,
            "sell_percentage": self.sell_percentage,
            "reference_price": self.reference_price,
            "average_cost": self.average_cost,
            "total_quantity_held": self.total_quantity_held,
            "last_action": self.last_action,
            "actions_history": self.actions_history or [],
            "total_profit_loss": self.total_profit_loss,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AutoTradingMonitor:
    """Monitors prices and executes automated trades"""

    @staticmethod
    def calculate_buy_trigger_price(reference_price: float, buy_percentage: float) -> float:
        """Calculate price at which to trigger buy order"""
        drop_amount = reference_price * (buy_percentage / 100)
        return reference_price - drop_amount

    @staticmethod
    def calculate_sell_trigger_price(average_cost: float, sell_percentage: float) -> float:
        """Calculate price at which to trigger sell order"""
        gain_amount = average_cost * (sell_percentage / 100)
        return average_cost + gain_amount

    @staticmethod
    def should_buy(
        current_price: float,
        buy_trigger_price: float,
        last_action_type: Optional[str] = None
    ) -> bool:
        """Determine if buy signal is triggered"""
        # Don't buy if we just sold (avoid rapid oscillation)
        if last_action_type == "SELL":
            return False
        return current_price <= buy_trigger_price

    @staticmethod
    def should_sell(
        current_price: float,
        sell_trigger_price: float,
        total_quantity_held: float,
        last_action_type: Optional[str] = None
    ) -> bool:
        """Determine if sell signal is triggered"""
        # Only sell if we hold quantity
        if total_quantity_held <= 0:
            return False
        # Don't sell if we just bought (avoid rapid oscillation)
        if last_action_type == "BUY":
            return False
        return current_price >= sell_trigger_price

    @staticmethod
    def calculate_profit_loss(
        quantity_sold: float,
        sell_price: float,
        average_cost: float
    ) -> float:
        """Calculate profit/loss from a sale"""
        return (sell_price - average_cost) * quantity_sold

    @staticmethod
    def update_average_cost(
        current_average: Optional[float],
        current_quantity: float,
        new_quantity: float,
        new_price: float
    ) -> tuple:
        """Calculate new average cost after buy"""
        if current_average is None:
            return new_price, new_quantity

        total_cost = (current_average * current_quantity) + (new_price * new_quantity)
        total_quantity = current_quantity + new_quantity
        new_average = total_cost / total_quantity if total_quantity > 0 else new_price

        return new_average, total_quantity


class AutoTradingExecutor:
    """Executes automated buy/sell orders"""

    @staticmethod
    def record_buy_action(
        settings: CryptoAutoTradingSettings,
        current_price: float,
        quantity: float
    ) -> AutoTradeAction:
        """Record a buy action"""
        # Update average cost
        new_avg, new_qty = AutoTradingMonitor.update_average_cost(
            settings.average_cost,
            settings.total_quantity_held,
            quantity,
            current_price
        )
        settings.average_cost = new_avg
        settings.total_quantity_held = new_qty

        action = AutoTradeAction(
            timestamp=datetime.utcnow().isoformat(),
            action_type="BUY",
            symbol=settings.symbol,
            price=current_price,
            quantity=quantity,
            reason=f"Auto-triggered at {current_price} (drop {settings.buy_percentage}%)"
        )
        return action

    @staticmethod
    def record_sell_action(
        settings: CryptoAutoTradingSettings,
        current_price: float,
        quantity: float
    ) -> AutoTradeAction:
        """Record a sell action"""
        # Calculate profit/loss
        pl = AutoTradingMonitor.calculate_profit_loss(
            quantity,
            current_price,
            settings.average_cost or current_price
        )

        # Update quantities
        settings.total_quantity_held -= quantity
        settings.total_profit_loss += pl

        if settings.total_quantity_held <= 0:
            settings.average_cost = None
            settings.total_quantity_held = 0

        action = AutoTradeAction(
            timestamp=datetime.utcnow().isoformat(),
            action_type="SELL",
            symbol=settings.symbol,
            price=current_price,
            quantity=quantity,
            profit_loss=pl,
            reason=f"Auto-triggered at {current_price} (gain {settings.sell_percentage}%)"
        )
        return action

    @staticmethod
    def record_config_action(
        settings: CryptoAutoTradingSettings,
        action_type: str,
        details: str
    ) -> AutoTradeAction:
        """Record configuration change"""
        action = AutoTradeAction(
            timestamp=datetime.utcnow().isoformat(),
            action_type=action_type,
            symbol=settings.symbol,
            price=0.0,
            reason=details
        )
        return action


# Trade execution quantities (percentage of portfolio)
DEFAULT_AUTO_TRADE_QUANTITY_PERCENT = 0.1  # 10% per trade
DEFAULT_BUY_PERCENTAGE = 5.0
DEFAULT_SELL_PERCENTAGE = 10.0
