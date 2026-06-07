"""
Robinhood Crypto Trading V2 API Client
======================================

Handles authenticated trading operations with Robinhood V2 API.
Requires: API key and private key from Robinhood Developer Portal.

API Documentation: https://trading.robinhood.com/
"""

import base64
import datetime
import json
import logging
from typing import Any, Dict, Optional, List
import uuid

import requests
from nacl.signing import SigningKey

# Configure logging
logger = logging.getLogger(__name__)

# Load from environment
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("ROBINHOOD_API_KEY", "")
BASE64_PRIVATE_KEY = os.getenv("ROBINHOOD_PRIVATE_KEY", "")


class CryptoAPITradingV2:
    """Robinhood Crypto Trading V2 API Client"""
    
    def __init__(self, api_key: Optional[str] = None, private_key_b64: Optional[str] = None):
        self.api_key = api_key or API_KEY
        self.private_key_b64 = private_key_b64 or BASE64_PRIVATE_KEY
        
        if not self.api_key or not self.private_key_b64:
            raise ValueError(
                "API key and private key required. "
                "Set ROBINHOOD_API_KEY and ROBINHOOD_PRIVATE_KEY in .env"
            )
        
        try:
            private_key_seed = base64.b64decode(self.private_key_b64)
            self.private_key = SigningKey(private_key_seed)
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise ValueError(f"Invalid private key: {e}")
        
        self.base_url = "https://trading.robinhood.com"

    @staticmethod
    def _get_current_timestamp() -> int:
        """Get current Unix timestamp in UTC"""
        return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

    @staticmethod
    def get_query_params(params_dict: Dict[str, Any]) -> str:
        """
        Build query parameter string from a dictionary.
        - Single values: {"key1": "value1", "key2": "value2"}
        - Multiple values for same key: {"symbol": ["BTC-USD", "ETH-USD"]}
        """
        if not params_dict:
            return ""
        
        params = []
        for key, value in params_dict.items():
            if value is None:
                continue
            if isinstance(value, list):
                # Handle multiple values for the same key
                for v in value:
                    params.append(f"{key}={v}")
            else:
                params.append(f"{key}={value}")
        
        return "?" + "&".join(params) if params else ""

    def make_api_request(self, method: str, path: str, body: str = "") -> Any:
        """Make authenticated API request with EdDSA signature"""
        timestamp = self._get_current_timestamp()
        headers = self.get_authorization_header(method, path, body, timestamp)
        url = self.base_url + path

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    json=json.loads(body) if body else None,
                    timeout=10
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check for non-success status codes
            if response.status_code >= 400:
                logger.warning(f"HTTP Error {response.status_code}: {response.reason}")
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {
                        "error": response.text or response.reason,
                        "status_code": response.status_code
                    }

            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"Error making API request: {e}")
            return {"error": str(e)}

    def get_authorization_header(
        self, method: str, path: str, body: str, timestamp: int
    ) -> Dict[str, str]:
        """Generate EdDSA signature headers for request"""
        message_to_sign = f"{self.api_key}{timestamp}{path}{method}{body}"
        signed = self.private_key.sign(message_to_sign.encode("utf-8"))

        return {
            "x-api-key": self.api_key,
            "x-signature": base64.b64encode(signed.signature).decode("utf-8"),
            "x-timestamp": str(timestamp),
        }

    # ============================================================================
    # Account Endpoints
    # ============================================================================

    def get_accounts(self) -> Dict[str, Any]:
        """Get all trading accounts"""
        path = "/api/v2/crypto/trading/accounts/"
        return self.make_api_request("GET", path)

    # ============================================================================
    # Market Data Endpoints
    # ============================================================================

    def get_trading_pairs(self, *symbols: Optional[str]) -> List[Dict[str, Any]]:
        """
        Get available trading pairs.
        
        Args:
            *symbols: Optional trading pair symbols (e.g., "BTC-USD", "ETH-USD")
                     If not provided, all pairs are returned
        
        Returns:
            List of trading pair information
        """
        params = {"symbol": list(symbols)} if symbols else {}
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/trading/trading_pairs/{query_params}"
        
        all_results = []
        response = self.make_api_request("GET", path)
        
        while response and "results" in response:
            results = response.get("results", [])
            all_results.extend(results)
            
            next_url = response.get("next")
            if not next_url:
                break
            
            next_path = next_url.replace(self.base_url, "")
            response = self.make_api_request("GET", next_path)
        
        return all_results

    def get_best_bid_ask(self, *symbols: str) -> Dict[str, Any]:
        """
        Get best bid/ask prices for symbols.
        
        Args:
            *symbols: Trading pair symbols (e.g., "BTC-USD", "ETH-USD")
        
        Returns:
            Best bid/ask data
        """
        params = {"symbol": list(symbols)} if symbols else {}
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/marketdata/best_bid_ask/{query_params}"
        return self.make_api_request("GET", path)

    def get_estimated_price(self, symbol: str, side: str, quantity: str) -> Dict[str, Any]:
        """
        Get estimated price for order.
        
        Args:
            symbol: Trading pair (e.g., "BTC-USD")
            side: "bid", "ask", or "both"
            quantity: Amount to trade (e.g., "0.1,1,1.999")
        
        Returns:
            Estimated price information
        """
        params = {"symbol": symbol, "side": side, "quantity": quantity}
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/trading/estimated_price/{query_params}"
        return self.make_api_request("GET", path)

    # ============================================================================
    # Holdings Endpoints
    # ============================================================================

    def get_holdings(self, account_number: str, *asset_codes: Optional[str]) -> Dict[str, Any]:
        """
        Get cryptocurrency holdings.
        
        Args:
            account_number: Account number
            *asset_codes: Optional asset codes (e.g., "BTC", "ETH")
                         If not provided, all holdings returned
        
        Returns:
            Holdings data
        """
        params = {"account_number": account_number}
        if asset_codes:
            params["asset_code"] = list(asset_codes)
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/trading/holdings/{query_params}"
        return self.make_api_request("GET", path)

    # ============================================================================
    # Order Management Endpoints
    # ============================================================================

    def place_order(
        self,
        account_number: str,
        side: str,
        order_type: str,
        symbol: str,
        order_config: Dict[str, str],
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            account_number: Account number
            side: "buy" or "sell"
            order_type: "market" or "limit"
            symbol: Trading pair (e.g., "BTC-USD")
            order_config: Order configuration dict
                For market orders: {"asset_quantity": "0.1"}
                For limit orders: {"asset_quantity": "0.1", "price": "50000"}
            client_order_id: Optional custom order ID (generated if not provided)
        
        Returns:
            Order confirmation
        """
        if not client_order_id:
            client_order_id = str(uuid.uuid4())
        
        body = {
            "client_order_id": client_order_id,
            "side": side,
            "type": order_type,
            "symbol": symbol,
            f"{order_type}_order_config": order_config,
        }
        params = {"account_number": account_number}
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/trading/orders/{query_params}"
        
        logger.info(f"Placing {side} order: {symbol} ({order_type})")
        return self.make_api_request("POST", path, json.dumps(body))

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an open order.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Cancellation confirmation
        """
        path = f"/api/v2/crypto/trading/orders/{order_id}/cancel/"
        logger.info(f"Cancelling order: {order_id}")
        return self.make_api_request("POST", path)

    def get_order(self, account_number: str, order_id: str) -> Dict[str, Any]:
        """
        Get order details.
        
        Args:
            account_number: Account number
            order_id: Order ID
        
        Returns:
            Order details
        """
        params = {"account_number": account_number}
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/trading/orders/{order_id}/{query_params}"
        return self.make_api_request("GET", path)

    def get_orders(
        self,
        account_number: str,
        created_at_start: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get order history.
        
        Args:
            account_number: Account number
            created_at_start: Start date (ISO format, e.g., "2023-01-01T00:00:00Z")
            status: Optional status filter (e.g., "filled", "cancelled")
        
        Returns:
            List of orders
        """
        params = {"account_number": account_number}
        if created_at_start:
            params["created_at_start"] = created_at_start
        if status:
            params["status"] = status
        
        query_params = self.get_query_params(params)
        path = f"/api/v2/crypto/trading/orders/{query_params}"
        return self.make_api_request("GET", path)


# Convenience functions for use in main.py

def get_rh_v2_client() -> CryptoAPITradingV2:
    """Get or create Robinhood V2 API client"""
    return CryptoAPITradingV2()


def place_robinhood_order_v2(
    account_number: str,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Helper function to place order on Robinhood V2 API.
    
    Args:
        account_number: Account number
        symbol: Trading pair (e.g., "BTC-USD")
        side: "buy" or "sell"
        order_type: "market" or "limit"
        quantity: Amount to trade
        price: Price (required for limit orders)
    
    Returns:
        Order confirmation
    """
    client = get_rh_v2_client()
    
    order_config = {"asset_quantity": str(quantity)}
    if order_type == "limit" and price:
        order_config["price"] = str(price)
    
    return client.place_order(
        account_number=account_number,
        side=side,
        order_type=order_type,
        symbol=symbol,
        order_config=order_config
    )
