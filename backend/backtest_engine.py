"""
Backtesting Engine
==================

Simulate trading strategies on historical data to evaluate performance
before risking real money.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Record of a trade during backtest"""
    entry_price: float
    entry_date: datetime
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    quantity: float = 1.0
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    status: str = "open"  # "open", "closed", "stopped_out"
    reason: str = ""


class BacktestEngine:
    """Run backtests on historical price data"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades: List[BacktestTrade] = []
        self.balance_history = [initial_capital]
    
    def run_backtest(
        self,
        symbol: str,
        price_history: List[Dict],  # [{"date": datetime, "price": float, "volume": float}, ...]
        strategy_func,  # Function that returns BUY/SELL/HOLD signal
        trade_size_pct: float = 0.1,  # 10% of capital per trade
        stop_loss_pct: float = 0.05,  # 5% stop loss
        take_profit_pct: float = 0.10  # 10% take profit
    ) -> Dict:
        """
        Run backtest on historical data
        
        Returns:
            {
                "symbol": str,
                "trades": [BacktestTrade],
                "total_profit_loss": float,
                "total_profit_loss_pct": float,
                "win_rate": float,
                "max_drawdown": float,
                "sharpe_ratio": float,
                "balance_history": [float],
                "metrics": {...}
            }
        """
        
        logger.info(f"🔄 Starting backtest for {symbol} with {len(price_history)} candles")
        
        # Reset state
        self.trades = []
        self.capital = self.initial_capital
        self.balance_history = [self.initial_capital]
        
        open_position = None
        
        # Process each candle
        for i, candle in enumerate(price_history):
            current_price = candle["price"]
            current_date = candle["date"]
            
            # Check for take profit or stop loss on open position
            if open_position:
                profit_loss = (current_price - open_position.entry_price) * open_position.quantity
                profit_loss_pct = (profit_loss / (open_position.entry_price * open_position.quantity)) * 100
                
                # Stop loss triggered
                if profit_loss_pct <= -stop_loss_pct:
                    open_position.exit_price = current_price
                    open_position.exit_date = current_date
                    open_position.profit_loss = profit_loss
                    open_position.profit_loss_pct = profit_loss_pct
                    open_position.status = "stopped_out"
                    self._close_position(open_position)
                    open_position = None
                
                # Take profit triggered
                elif profit_loss_pct >= take_profit_pct:
                    open_position.exit_price = current_price
                    open_position.exit_date = current_date
                    open_position.profit_loss = profit_loss
                    open_position.profit_loss_pct = profit_loss_pct
                    open_position.status = "closed"
                    self._close_position(open_position)
                    open_position = None
            
            # Generate signal
            try:
                signal = strategy_func(price_history[:i+1])
            except Exception as e:
                logger.warning(f"Signal generation error at {current_date}: {e}")
                continue
            
            # Execute signal
            if signal == "BUY" and not open_position:
                trade_amount = self.capital * trade_size_pct
                quantity = trade_amount / current_price
                
                open_position = BacktestTrade(
                    entry_price=current_price,
                    entry_date=current_date,
                    quantity=quantity,
                    reason="Signal"
                )
                self.capital -= trade_amount
                logger.debug(f"📈 BUY {quantity:.6f} @ ${current_price} on {current_date}")
            
            elif signal == "SELL" and open_position:
                profit_loss = (current_price - open_position.entry_price) * open_position.quantity
                trade_proceeds = current_price * open_position.quantity
                
                open_position.exit_price = current_price
                open_position.exit_date = current_date
                open_position.profit_loss = profit_loss
                open_position.profit_loss_pct = (profit_loss / (open_position.entry_price * open_position.quantity)) * 100
                open_position.status = "closed"
                
                self._close_position(open_position)
                open_position = None
                logger.debug(f"📉 SELL @ ${current_price} on {current_date}, P&L: ${profit_loss:.2f}")
            
            # Record balance
            if open_position:
                portfolio_value = self.capital + (current_price * open_position.quantity)
            else:
                portfolio_value = self.capital
            
            self.balance_history.append(portfolio_value)
        
        # Close open position at end of backtest
        if open_position and price_history:
            final_price = price_history[-1]["price"]
            profit_loss = (final_price - open_position.entry_price) * open_position.quantity
            open_position.exit_price = final_price
            open_position.exit_date = price_history[-1]["date"]
            open_position.profit_loss = profit_loss
            open_position.profit_loss_pct = (profit_loss / (open_position.entry_price * open_position.quantity)) * 100
            open_position.status = "closed"
            self._close_position(open_position)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        logger.info(f"✅ Backtest complete: {len(self.trades)} trades, P&L: ${metrics['total_profit_loss']:.2f}")
        
        return {
            "symbol": symbol,
            "trades": [self._trade_to_dict(t) for t in self.trades],
            "total_profit_loss": metrics["total_profit_loss"],
            "total_profit_loss_pct": metrics["total_profit_loss_pct"],
            "win_rate": metrics["win_rate"],
            "max_drawdown": metrics["max_drawdown"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "balance_history": self.balance_history,
            "metrics": metrics
        }
    
    def _close_position(self, position: BacktestTrade):
        """Record closed position"""
        self.trades.append(position)
        if position.profit_loss:
            self.capital += position.entry_price * position.quantity + position.profit_loss
    
    def _calculate_metrics(self) -> Dict:
        """Calculate backtest performance metrics"""
        
        if not self.trades:
            return {
                "total_profit_loss": 0.0,
                "total_profit_loss_pct": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "num_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0
            }
        
        # Basic P&L
        total_pl = sum(t.profit_loss or 0 for t in self.trades)
        total_pl_pct = (total_pl / self.initial_capital) * 100
        
        # Win rate
        winning_trades = [t for t in self.trades if (t.profit_loss or 0) > 0]
        losing_trades = [t for t in self.trades if (t.profit_loss or 0) < 0]
        win_rate = (len(winning_trades) / len(self.trades) * 100) if self.trades else 0
        
        # Average win/loss
        avg_win = (sum(t.profit_loss or 0 for t in winning_trades) / len(winning_trades)) if winning_trades else 0
        avg_loss = (sum(abs(t.profit_loss or 0) for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        # Profit factor
        total_wins = sum(t.profit_loss or 0 for t in winning_trades)
        total_losses = sum(abs(t.profit_loss or 0) for t in losing_trades)
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Sharpe ratio (simplified)
        returns = self._calculate_returns()
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        
        return {
            "total_profit_loss": total_pl,
            "total_profit_loss_pct": total_pl_pct,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "num_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if not self.balance_history or len(self.balance_history) < 2:
            return 0.0
        
        max_balance = max(self.balance_history)
        min_balance = min(self.balance_history)
        
        if max_balance == 0:
            return 0.0
        
        max_drawdown_pct = ((max_balance - min_balance) / max_balance) * 100
        return max_drawdown_pct
    
    def _calculate_returns(self) -> List[float]:
        """Calculate daily returns"""
        returns = []
        for i in range(1, len(self.balance_history)):
            if self.balance_history[i-1] > 0:
                ret = ((self.balance_history[i] - self.balance_history[i-1]) / self.balance_history[i-1])
                returns.append(ret)
        return returns
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        import statistics
        avg_return = statistics.mean(returns)
        std_dev = statistics.stdev(returns)
        
        if std_dev == 0:
            return 0.0
        
        sharpe = (avg_return - (risk_free_rate / 252)) / std_dev * (252 ** 0.5)
        return sharpe
    
    @staticmethod
    def _trade_to_dict(trade: BacktestTrade) -> Dict:
        """Convert trade to dictionary"""
        return {
            "entry_price": trade.entry_price,
            "entry_date": trade.entry_date.isoformat() if isinstance(trade.entry_date, datetime) else str(trade.entry_date),
            "exit_price": trade.exit_price,
            "exit_date": trade.exit_date.isoformat() if isinstance(trade.exit_date, datetime) else str(trade.exit_date),
            "quantity": trade.quantity,
            "profit_loss": trade.profit_loss,
            "profit_loss_pct": trade.profit_loss_pct,
            "status": trade.status,
            "reason": trade.reason
        }
