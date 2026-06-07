"""
Binance API Integration Module
==============================

Handles real-time crypto trading, market data, and account management through Binance.
Requires: API key and API secret from Binance account.

API Documentation: https://binance-docs.github.io/apidocs/
"""

import os
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Try to import python-binance, provide helpful error if missing
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
except ImportError:
    raise ImportError(
        "python-binance is not installed. Install it with: pip install python-binance"
    )

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global Binance client
_client = None
_client_config: Optional[Tuple[str, str, bool]] = None


class BinanceError(Exception):
    """Binance API error."""
    pass


def get_client() -> Client:
    """
    Get or create Binance client.
    
    Returns:
        Binance Client instance
        
    Raises:
        BinanceError: If credentials not configured
    """
    global _client, _client_config

    # Reload environment values so runtime updates do not require process restart.
    load_dotenv(override=False)
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    tld = os.getenv("BINANCE_TLD", "com").strip().lower() or "com"
    current_config = (api_key, api_secret, testnet, tld)

    if _client is not None and _client_config == current_config:
        return _client

    if not api_key or not api_secret:
        raise BinanceError(
            "Binance credentials not configured. Set BINANCE_API_KEY and BINANCE_API_SECRET in .env"
        )

    try:
        _client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            tld=tld
        )
        _client_config = current_config
        logger.info(f"Connected to Binance ({'testnet' if testnet else 'mainnet'}, tld={tld})")
        return _client
    except Exception as e:
        raise BinanceError(f"Failed to connect to Binance: {e}")


def is_connected() -> bool:
    """Check if Binance connection is active."""
    try:
        client = get_client()
        client.get_server_time()
        return True
    except:
        return False


# ============================================================================
# Account & Portfolio Functions
# ============================================================================

def get_account_info() -> Dict:
    """
    Get account information including balances.
    
    Returns:
        Account data with balances and trading status
    """
    try:
        client = get_client()
        account = client.get_account()
        
        return {
            "can_trade": account["canTrade"],
            "can_deposit": account["canDeposit"],
            "can_withdraw": account["canWithdraw"],
            "update_time": account["updateTime"],
            "balances": account["balances"],
            "maker_commission": account["makerCommission"],
            "taker_commission": account["takerCommission"]
        }
    except BinanceAPIException as e:
        logger.error(f"Binance API error: {e}")
        raise BinanceError(f"Failed to get account info: {e}")


def get_balance(asset: str = None) -> Dict:
    """
    Get balance for specific asset or all assets.
    
    Args:
        asset: Asset symbol (e.g., 'BTC', 'USDT'). If None, returns all balances.
        
    Returns:
        Balance information
    """
    try:
        client = get_client()
        account = client.get_account()
        
        if asset:
            asset = asset.upper()
            for balance in account["balances"]:
                if balance["asset"] == asset:
                    return {
                        "asset": asset,
                        "free": float(balance["free"]),
                        "locked": float(balance["locked"]),
                        "total": float(balance["free"]) + float(balance["locked"])
                    }
            raise BinanceError(f"Asset {asset} not found")
        else:
            # Return all balances with non-zero amounts
            balances = []
            for balance in account["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked
                
                if total > 0:
                    balances.append({
                        "asset": balance["asset"],
                        "free": free,
                        "locked": locked,
                        "total": total
                    })
            return sorted(balances, key=lambda x: x["total"], reverse=True)
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get balance: {e}")


def get_portfolio_value(base_currency: str = "USDT") -> Dict:
    """
    Calculate total portfolio value in specified currency.
    
    Args:
        base_currency: Currency to value portfolio in (default: USDT)
        
    Returns:
        Portfolio valuation
    """
    try:
        client = get_client()
        account = client.get_account()
        
        total_value = 0.0
        holdings = []
        
        for balance in account["balances"]:
            free = float(balance["free"])
            locked = float(balance["locked"])
            total = free + locked
            
            if total == 0:
                continue
            
            asset = balance["asset"]
            
            # Get price in base currency
            if asset == base_currency:
                price = 1.0
            else:
                try:
                    ticker = client.get_symbol_info(f"{asset}{base_currency}")
                    if ticker:
                        price_data = client.get_average_price(symbol=f"{asset}{base_currency}")
                        price = float(price_data["price"])
                    else:
                        price = 0
                except:
                    price = 0
            
            value = total * price
            total_value += value
            
            if value > 0:
                holdings.append({
                    "asset": asset,
                    "quantity": total,
                    "price": price,
                    "value": value,
                    "percentage": 0  # Will calculate after total
                })
        
        # Calculate percentages
        for holding in holdings:
            holding["percentage"] = (holding["value"] / total_value * 100) if total_value > 0 else 0
        
        return {
            "total_value": total_value,
            "base_currency": base_currency,
            "holdings": sorted(holdings, key=lambda x: x["value"], reverse=True),
            "updated_at": datetime.now().isoformat()
        }
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get portfolio value: {e}")


# ============================================================================
# Market Data Functions
# ============================================================================

def get_ticker(symbol: str) -> Dict:
    """
    Get 24hr ticker price change statistics.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        
    Returns:
        Ticker data with price, volume, changes
    """
    try:
        client = get_client()
        ticker = client.get_symbol_ticker(symbol=symbol.upper())
        stats = client.get_24hr_ticker_price_change_statistics(symbol=symbol.upper())
        
        return {
            "symbol": symbol.upper(),
            "price": float(ticker["price"]),
            "bid": float(stats["bidPrice"]),
            "ask": float(stats["askPrice"]),
            "high_24h": float(stats["highPrice"]),
            "low_24h": float(stats["lowPrice"]),
            "volume": float(stats["volume"]),
            "quote_volume": float(stats["quoteAssetVolume"]),
            "price_change": float(stats["priceChange"]),
            "price_change_percent": float(stats["priceChangePercent"]),
            "timestamp": datetime.now().isoformat()
        }
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get ticker for {symbol}: {e}")


def get_klines(symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict]:
    """
    Get candlestick data (OHLC).
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        interval: Time interval ('1m', '5m', '15m', '1h', '4h', '1d', etc.)
        limit: Number of candles to retrieve (max 1000)
        
    Returns:
        List of candlesticks with OHLCV data
    """
    try:
        client = get_client()
        klines = client.get_klines(symbol=symbol.upper(), interval=interval, limit=min(limit, 1000))
        
        result = []
        for k in klines:
            result.append({
                "open_time": datetime.fromtimestamp(k[0] / 1000).isoformat(),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": datetime.fromtimestamp(k[6] / 1000).isoformat(),
                "quote_volume": float(k[7])
            })
        
        return result
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get klines for {symbol}: {e}")


def get_top_gainers(limit: int = 10) -> List[Dict]:
    """
    Get top gaining cryptocurrencies.
    
    Args:
        limit: Number of results
        
    Returns:
        List of top gainers
    """
    try:
        client = get_client()
        
        # Get all symbols
        exchange_info = client.get_exchange_info()
        symbols = [s["symbol"] for s in exchange_info["symbols"] if s["symbol"].endswith("USDT")]
        
        # Get 24hr stats for all
        gainers = []
        for symbol in symbols[:limit * 3]:  # Get more to filter
            try:
                stats = client.get_24hr_ticker_price_change_statistics(symbol=symbol)
                change_percent = float(stats["priceChangePercent"])
                
                gainers.append({
                    "symbol": symbol,
                    "price": float(stats["lastPrice"]),
                    "change_percent": change_percent,
                    "volume": float(stats["quoteAssetVolume"])
                })
            except:
                continue
        
        # Sort by change percent and return top
        return sorted(gainers, key=lambda x: x["change_percent"], reverse=True)[:limit]
    
    except BinanceAPIException as e:
        logger.error(f"Failed to get top gainers: {e}")
        return []


# ============================================================================
# Trading Functions
# ============================================================================

def place_order(
    symbol: str,
    side: str,  # 'BUY' or 'SELL'
    order_type: str,  # 'LIMIT' or 'MARKET'
    quantity: float,
    price: Optional[float] = None,
    time_in_force: str = "GTC"
) -> Dict:
    """
    Place an order.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        side: 'BUY' or 'SELL'
        order_type: 'LIMIT' or 'MARKET'
        quantity: Amount to buy/sell
        price: Price per unit (required for LIMIT orders)
        time_in_force: 'GTC' (good til cancel), 'IOC', etc.
        
    Returns:
        Order confirmation
    """
    try:
        if side.upper() not in ["BUY", "SELL"]:
            raise ValueError("side must be 'BUY' or 'SELL'")
        
        if order_type.upper() not in ["LIMIT", "MARKET"]:
            raise ValueError("order_type must be 'LIMIT' or 'MARKET'")
        
        if order_type.upper() == "LIMIT" and price is None:
            raise ValueError("price required for LIMIT orders")
        
        client = get_client()
        
        if order_type.upper() == "MARKET":
            order = client.order_market(
                symbol=symbol.upper(),
                side=side.upper(),
                quantity=quantity
            )
        else:
            order = client.order_limit(
                symbol=symbol.upper(),
                side=side.upper(),
                timeInForce=time_in_force,
                quantity=quantity,
                price=price
            )
        
        logger.info(f"Order placed: {order['orderId']}")
        
        return {
            "order_id": order["orderId"],
            "symbol": order["symbol"],
            "side": order["side"],
            "quantity": float(order["origQty"]),
            "price": float(order.get("price", 0)),
            "status": order["status"],
            "timestamp": datetime.fromtimestamp(order["time"] / 1000).isoformat()
        }
    
    except BinanceOrderException as e:
        logger.error(f"Order error: {e}")
        raise BinanceError(f"Failed to place order: {e}")
    except BinanceAPIException as e:
        logger.error(f"API error: {e}")
        raise BinanceError(f"API error: {e}")


def cancel_order(symbol: str, order_id: int) -> Dict:
    """
    Cancel an open order.
    
    Args:
        symbol: Trading pair
        order_id: Order ID to cancel
        
    Returns:
        Cancellation confirmation
    """
    try:
        client = get_client()
        result = client.cancel_order(symbol=symbol.upper(), orderId=order_id)
        
        logger.info(f"Order {order_id} cancelled")
        
        return {
            "order_id": result["orderId"],
            "symbol": result["symbol"],
            "status": result["status"],
            "timestamp": datetime.now().isoformat()
        }
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to cancel order: {e}")


def get_order_status(symbol: str, order_id: int) -> Dict:
    """
    Get status of a specific order.
    
    Args:
        symbol: Trading pair
        order_id: Order ID
        
    Returns:
        Order details
    """
    try:
        client = get_client()
        order = client.get_order(symbol=symbol.upper(), orderId=order_id)
        
        return {
            "order_id": order["orderId"],
            "symbol": order["symbol"],
            "side": order["side"],
            "quantity": float(order["origQty"]),
            "executed_quantity": float(order["executedQty"]),
            "price": float(order["price"]),
            "status": order["status"],
            "timestamp": datetime.fromtimestamp(order["time"] / 1000).isoformat(),
            "update_time": datetime.fromtimestamp(order["updateTime"] / 1000).isoformat()
        }
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get order status: {e}")


def get_open_orders(symbol: str = None) -> List[Dict]:
    """
    Get list of open orders.
    
    Args:
        symbol: (Optional) Filter by trading pair
        
    Returns:
        List of open orders
    """
    try:
        client = get_client()
        
        if symbol:
            orders = client.get_open_orders(symbol=symbol.upper())
        else:
            orders = client.get_open_orders()
        
        result = []
        for order in orders:
            result.append({
                "order_id": order["orderId"],
                "symbol": order["symbol"],
                "side": order["side"],
                "quantity": float(order["origQty"]),
                "executed_quantity": float(order["executedQty"]),
                "price": float(order["price"]),
                "status": order["status"],
                "timestamp": datetime.fromtimestamp(order["time"] / 1000).isoformat()
            })
        
        return result
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get open orders: {e}")


def get_order_history(symbol: str = None, limit: int = 20) -> List[Dict]:
    """
    Get order history.
    
    Args:
        symbol: (Optional) Filter by trading pair
        limit: Number of orders to retrieve
        
    Returns:
        List of past orders
    """
    try:
        client = get_client()
        
        if symbol:
            orders = client.get_all_orders(symbol=symbol.upper(), limit=limit)
        else:
            orders = client.get_all_orders(limit=limit)
        
        result = []
        for order in orders:
            result.append({
                "order_id": order["orderId"],
                "symbol": order["symbol"],
                "side": order["side"],
                "quantity": float(order["origQty"]),
                "executed_quantity": float(order["executedQty"]),
                "price": float(order["price"]),
                "status": order["status"],
                "timestamp": datetime.fromtimestamp(order["time"] / 1000).isoformat()
            })
        
        return sorted(result, key=lambda x: x["timestamp"], reverse=True)
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get order history: {e}")


# ============================================================================
# Trading Pairs & Market Info
# ============================================================================

def get_trading_pairs(quote_asset: str = "USDT", limit: int = 100) -> List[Dict]:
    """
    Get available trading pairs.
    
    Args:
        quote_asset: Filter by quote asset (e.g., 'USDT', 'BUSD')
        limit: Maximum pairs to return
        
    Returns:
        List of trading pairs
    """
    try:
        client = get_client()
        exchange_info = client.get_exchange_info()
        
        pairs = []
        for symbol in exchange_info["symbols"]:
            if symbol["symbol"].endswith(quote_asset.upper()) and symbol["status"] == "TRADING":
                pairs.append({
                    "symbol": symbol["symbol"],
                    "base_asset": symbol["baseAsset"],
                    "quote_asset": symbol["quoteAsset"],
                    "status": symbol["status"]
                })
        
        return pairs[:limit]
    
    except BinanceAPIException as e:
        raise BinanceError(f"Failed to get trading pairs: {e}")


def search_symbol(query: str) -> List[Dict]:
    """
    Search for trading pair by name or symbol.
    
    Args:
        query: Symbol or name to search
        
    Returns:
        Matching trading pairs
    """
    try:
        client = get_client()
        exchange_info = client.get_exchange_info()
        
        query_upper = query.upper()
        results = []
        
        for symbol in exchange_info["symbols"]:
            if (query_upper in symbol["symbol"] and 
                symbol["symbol"].endswith("USDT") and
                symbol["status"] == "TRADING"):
                results.append({
                    "symbol": symbol["symbol"],
                    "base_asset": symbol["baseAsset"],
                    "quote_asset": symbol["quoteAsset"]
                })
        
        return results[:10]
    
    except BinanceAPIException as e:
        raise BinanceError(f"Search failed: {e}")
