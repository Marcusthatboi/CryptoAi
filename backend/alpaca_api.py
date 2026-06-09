"""
Alpaca Trading API Integration Module
======================================

Handles authentication and trading operations with Alpaca Trading API.
Uses Legacy authentication (API Key ID + Secret Key in headers).
Supports both paper and live trading accounts.
"""

import os
import logging
import requests
from types import SimpleNamespace
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Session storage for API client
_alpaca_client = None

def _get_credentials():
    """Load credentials from environment variables"""
    key_id = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    base_url = os.getenv("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets")
    return key_id, secret_key, base_url

# Backward compatibility - load at module level but will be updated dynamically
ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY, ALPACA_API_BASE_URL = _get_credentials()


class AlpacaAuthError(Exception):
    """Raised when authentication with Alpaca fails"""
    pass


class AlpacaAPIError(Exception):
    """Raised when an Alpaca API call fails"""
    pass


def _to_namespace(payload):
    """Convert dictionaries/lists into attribute-accessible objects."""
    if isinstance(payload, dict):
        return SimpleNamespace(**{k: _to_namespace(v) for k, v in payload.items()})
    if isinstance(payload, list):
        return [_to_namespace(item) for item in payload]
    return payload


class AlpacaRESTFallback:
    """Minimal Alpaca REST client used when alpaca-trade-api is unavailable."""

    def __init__(self, key_id: str, secret_key: str, base_url: str):
        self.base_url = str(base_url or "").rstrip("/")
        self.headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
        }

    def _request(self, method: str, path: str, params: Dict = None, json_body: Dict = None):
        response = requests.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            json=json_body,
            timeout=15,
        )
        if response.status_code >= 400:
            raise AlpacaAPIError(
                f"Alpaca REST error {response.status_code} on {path}: {response.text[:300]}"
            )
        if response.status_code == 204:
            return None
        return response.json()

    def get_account(self):
        return _to_namespace(self._request("GET", "/v2/account"))

    def list_positions(self):
        return _to_namespace(self._request("GET", "/v2/positions"))

    def get_latest_crypto_quotes(self, symbols: List[str]):
        symbol_value = ",".join(symbols or [])
        payload = self._request(
            "GET",
            "/v1beta3/crypto/us/latest/quotes",
            params={"symbols": symbol_value},
        )
        quotes = (payload or {}).get("quotes", {})
        return {key: _to_namespace(value) for key, value in quotes.items()}

    def submit_order(self, symbol: str, qty: float, side: str, type: str, time_in_force: str):
        payload = self._request(
            "POST",
            "/v2/orders",
            json_body={
                "symbol": symbol,
                "qty": str(qty),
                "side": side,
                "type": type,
                "time_in_force": time_in_force,
            },
        )
        return _to_namespace(payload)

    def cancel_order(self, order_id: str):
        self._request("DELETE", f"/v2/orders/{order_id}")

    def list_orders(self, status: str = "all"):
        payload = self._request("GET", "/v2/orders", params={"status": status, "direction": "desc"})
        return _to_namespace(payload)

    def get_order(self, order_id: str):
        return _to_namespace(self._request("GET", f"/v2/orders/{order_id}"))


def get_alpaca_client():
    """Get or create Alpaca API client using Trading API credentials"""
    global _alpaca_client
    
    # ALWAYS reload environment variables to get fresh values
    # This ensures we pick up any updates to the .env file
    load_dotenv(override=True)
    
    # Always get fresh credentials from environment
    key_id, secret_key, base_url = _get_credentials()
    
    # Skip caching if credentials are placeholder values
    if key_id and key_id.startswith("your_") or secret_key and secret_key.startswith("your_"):
        logger.warning("Credentials are placeholder values, not caching client")
        _alpaca_client = None
    elif _alpaca_client is not None:
        return _alpaca_client
    
    if not key_id or not secret_key:
        logger.error("Missing Alpaca API credentials")
        raise AlpacaAuthError(
            "Missing Alpaca Trading API credentials. Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env"
        )
    
    try:
        logger.info(f"Creating Alpaca REST client (paper trading mode)")
        logger.info(f"  Base URL: {base_url}")
        
        # Prefer official SDK when available; use HTTP fallback otherwise.
        try:
            from alpaca_trade_api import REST

            _alpaca_client = REST(
                key_id=key_id,
                secret_key=secret_key,
                base_url=base_url,
                api_version="v2"
            )
            logger.info("Using alpaca-trade-api SDK client")
        except ImportError:
            logger.warning("alpaca-trade-api unavailable; using direct REST fallback client")
            _alpaca_client = AlpacaRESTFallback(key_id=key_id, secret_key=secret_key, base_url=base_url)
        
        logger.info("Successfully connected to Alpaca Trading API")
        return _alpaca_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Alpaca client: {str(e)}")
        raise AlpacaAuthError(f"Failed to connect to Alpaca: {str(e)}")


def is_authenticated() -> bool:
    """Check if authenticated with Alpaca"""
    try:
        # Get fresh credentials each time
        key_id, secret_key, _base_url = _get_credentials()
        
        logger.info(f"is_authenticated() called")
        logger.info("Alpaca credentials present: %s", bool(key_id and secret_key))
        
        client = get_alpaca_client()
        logger.info(f"Got client: {client}")
        
        account = client.get_account()
        logger.info(f"Got account: {account}")
        logger.info("Successfully authenticated with Alpaca")
        return account is not None
    except AlpacaAuthError as e:
        logger.warning(f"Alpaca authentication check failed with AlpacaAuthError: {str(e)}")
        return False
    except Exception as e:
        import traceback
        logger.warning(f"Alpaca connection check failed with Exception: {str(e)}")
        logger.warning(traceback.format_exc())
        return False


def get_account_info() -> Dict:
    """Get account information"""
    try:
        client = get_alpaca_client()
        account = client.get_account()
        
        # Build response with only the most common/reliable attributes
        # Convert account object to dict for safe access
        account_dict = account.dict() if hasattr(account, 'dict') else {}
        
        result = {
            "status": "success",
            "account_id": account.id if hasattr(account, 'id') else None,
            "buying_power": float(account.buying_power) if hasattr(account, 'buying_power') else None,
            "cash": float(account.cash) if hasattr(account, 'cash') else None,
            "equity": float(account.equity) if hasattr(account, 'equity') else None,
        }
        
        return result
    except Exception as e:
        logger.error(f"Error fetching account info: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise AlpacaAPIError(f"Failed to fetch account info: {str(e)}")


def get_holdings() -> Dict:
    """Get current holdings (open positions)"""
    try:
        client = get_alpaca_client()
        positions = client.list_positions()  # Use list_positions instead of get_positions
        
        holdings = []
        for position in positions:
            holding = {
                "symbol": position.symbol if hasattr(position, 'symbol') else None,
            }
            if hasattr(position, 'qty'):
                holding["quantity"] = float(position.qty)
            if hasattr(position, 'avg_entry_price'):
                holding["avg_entry_price"] = float(position.avg_entry_price)
            if hasattr(position, 'current_price'):
                holding["current_price"] = float(position.current_price)
            if hasattr(position, 'market_value'):
                holding["market_value"] = float(position.market_value)
            if hasattr(position, 'unrealized_pl'):
                holding["unrealized_pl"] = float(position.unrealized_pl)
            if hasattr(position, 'side'):
                holding["side"] = position.side
            holdings.append(holding)
        
        total_value = sum(h.get("market_value", 0) for h in holdings)
        return {
            "status": "success",
            "holdings": holdings,
            "total_value": total_value,
        }
    except Exception as e:
        logger.error(f"Error fetching holdings: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise AlpacaAPIError(f"Failed to fetch holdings: {str(e)}")


def get_crypto_quote(symbol: str) -> Dict:
    """Get real-time quote for a cryptocurrency"""
    try:
        client = get_alpaca_client()
        
        # Alpaca crypto symbols are formatted as CRYPTO/USD or CRYPTO/USDT
        if not symbol.endswith("/USD") and not symbol.endswith("/USDT"):
            symbol = f"{symbol.upper()}/USD"
        else:
            symbol = symbol.upper()
        
        quotes = client.get_latest_crypto_quotes([symbol])
        
        if not quotes or symbol not in quotes:
            raise AlpacaAPIError(f"No quote data available for {symbol}")
        
        quote = quotes[symbol]
        
        result = {
            "status": "success",
            "symbol": symbol,
        }
        # Alpaca crypto quote attributes are: 'ap' (ask), 'as' (ask size), 'bp' (bid), 'bs' (bid size), 't' (timestamp)
        if hasattr(quote, 'bp'):
            result["bid"] = float(quote.bp)
        if hasattr(quote, 'ap'):
            result["ask"] = float(quote.ap)
        if hasattr(quote, 'ap'):  # Use ask price as last_price if not available
            result["last_price"] = float(quote.ap)
        if hasattr(quote, 't'):
            result["timestamp"] = str(quote.t)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise AlpacaAPIError(f"Failed to fetch quote: {str(e)}")


def place_order(
    symbol: str,
    qty: float,
    side: str = "buy",
    order_type: str = "market",
    time_in_force: str = "day",
) -> Dict:
    """Place a trading order"""
    try:
        client = get_alpaca_client()
        
        # Ensure symbol is in correct format for Alpaca crypto
        if not symbol.endswith("/USD"):
            symbol = f"{symbol.upper()}/USD"
        
        if side.lower() not in ["buy", "sell"]:
            raise ValueError("side must be 'buy' or 'sell'")
        
        order = client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side.lower(),
            type=order_type.lower(),
            time_in_force=time_in_force.lower(),
        )
        
        return {
            "status": "success",
            "order_id": order.id,
            "symbol": order.symbol,
            "quantity": float(order.qty),
            "side": order.side,
            "order_type": order.order_type,
            "status": order.status,
            "filled_at": order.filled_at,
        }
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        raise AlpacaAPIError(f"Failed to place order: {str(e)}")


def cancel_order(order_id: str) -> Dict:
    """Cancel an open order"""
    try:
        client = get_alpaca_client()
        client.cancel_order(order_id)
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": f"Order {order_id} cancelled successfully",
        }
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {str(e)}")
        raise AlpacaAPIError(f"Failed to cancel order: {str(e)}")


def get_orders(status: str = "all") -> Dict:
    """Get orders (open, closed, all)"""
    try:
        client = get_alpaca_client()
        orders = client.list_orders(status=status)  # Use list_orders instead of get_orders
        
        order_list = []
        for order in orders:
            order_data = {
                "id": order.id if hasattr(order, 'id') else None,
            }
            if hasattr(order, 'symbol'):
                order_data["symbol"] = order.symbol
            if hasattr(order, 'qty'):
                order_data["quantity"] = float(order.qty)
            if hasattr(order, 'side'):
                order_data["side"] = order.side
            if hasattr(order, 'order_type'):
                order_data["type"] = order.order_type
            if hasattr(order, 'status'):
                order_data["status"] = order.status
            if hasattr(order, 'created_at'):
                order_data["created_at"] = str(order.created_at)
            if hasattr(order, 'filled_at') and order.filled_at:
                order_data["filled_at"] = str(order.filled_at)
            if hasattr(order, 'filled_qty'):
                order_data["filled_qty"] = float(order.filled_qty)
            
            order_list.append(order_data)
        
        return {
            "status": "success",
            "orders": order_list,
            "total_count": len(order_list),
        }
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise AlpacaAPIError(f"Failed to fetch orders: {str(e)}")


def get_order_status(order_id: str) -> Dict:
    """Get status of a specific order"""
    try:
        client = get_alpaca_client()
        order = client.get_order(order_id)
        
        return {
            "status": "success",
            "id": order.id,
            "symbol": order.symbol,
            "quantity": float(order.qty),
            "filled_qty": float(order.filled_qty),
            "side": order.side,
            "type": order.order_type,
            "order_status": order.status,
            "created_at": order.created_at,
            "filled_at": order.filled_at,
        }
    except Exception as e:
        logger.error(f"Error fetching order status: {str(e)}")
        raise AlpacaAPIError(f"Failed to fetch order status: {str(e)}")
