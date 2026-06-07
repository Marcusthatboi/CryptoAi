"""
Robinhood API Integration Module
==================================

Handles OAuth 2.0 authentication and trading operations with Robinhood.
Requires: API key, secret, and private/public keys from Robinhood Developer Portal.
"""

import requests
import logging
import json
import time
import base64
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import os
from dotenv import load_dotenv

# EdDSA signature support
try:
    import nacl.signing
except ImportError:
    nacl = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Robinhood API Configuration
ROBINHOOD_API_BASE = "https://api.robinhood.com"
ROBINHOOD_OAUTH_URL = f"{ROBINHOOD_API_BASE}/oauth2"
ROBINHOOD_AUTH_URL = f"{ROBINHOOD_OAUTH_URL}/authorize"
ROBINHOOD_TOKEN_URL = f"{ROBINHOOD_OAUTH_URL}/token"

# OAuth 2.0 Configuration (from environment variables)
ROBINHOOD_CLIENT_ID = os.getenv("ROBINHOOD_CLIENT_ID")
ROBINHOOD_CLIENT_SECRET = os.getenv("ROBINHOOD_CLIENT_SECRET")
ROBINHOOD_REDIRECT_URI = os.getenv("ROBINHOOD_REDIRECT_URI", "http://localhost:8000/auth/robinhood/callback")

# API Signature Configuration (for authenticated requests)
ROBINHOOD_PRIVATE_KEY = os.getenv("ROBINHOOD_PRIVATE_KEY")  # Base64 encoded
ROBINHOOD_API_KEY = os.getenv("ROBINHOOD_API_KEY")

# Token storage
TOKEN_FILE = Path(__file__).parent.parent / ".robinhood_token.json"


class RobinhoodAuthError(Exception):
    """Robinhood authentication error."""
    pass


class RobinhoodAPIError(Exception):
    """Robinhood API error."""
    pass


# ============================================================================
# Request Signing (EdDSA)
# ============================================================================

def _generate_signature(
    api_key: str,
    private_key_base64: str,
    path: str,
    method: str,
    body: Optional[Dict] = None,
    timestamp: Optional[int] = None
) -> str:
    """
    Generate EdDSA signature for Robinhood API request.
    
    Args:
        api_key: API key string
        private_key_base64: Private key in base64 format
        path: Request path (e.g., '/api/v1/crypto/trading/orders/')
        method: HTTP method (GET, POST, etc.)
        body: Request body as dict (optional)
        timestamp: Unix timestamp (uses current time if not provided)
        
    Returns:
        Base64-encoded signature
        
    Raises:
        RobinhoodAPIError: If signature generation fails
    """
    if not nacl:
        raise RobinhoodAPIError("pynacl is required for request signing. Install with: pip install pynacl")
    
    try:
        # Use current timestamp if not provided
        if timestamp is None:
            timestamp = int(time.time())
        
        # Convert private key from base64
        private_key_seed = base64.b64decode(private_key_base64)
        private_key = nacl.signing.SigningKey(private_key_seed)
        
        # Create message to sign
        body_str = json.dumps(body) if body else ""
        message = f"{api_key}{timestamp}{path}{method}{body_str}"
        
        # Sign message
        signed = private_key.sign(message.encode("utf-8"))
        
        # Return base64-encoded signature
        return base64.b64encode(signed.signature).decode("utf-8")
    
    except Exception as e:
        logger.error(f"Signature generation failed: {e}")
        raise RobinhoodAPIError(f"Failed to generate signature: {e}")


def _make_signed_request(
    method: str,
    path: str,
    body: Optional[Dict] = None,
    params: Optional[Dict] = None,
    timeout: int = 10
) -> requests.Response:
    """
    Make a signed request to Robinhood API.
    
    Args:
        method: HTTP method
        path: API path
        body: Request body (for POST/PUT)
        params: Query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response object
        
    Raises:
        RobinhoodAPIError: If credentials missing or request fails
    """
    if not ROBINHOOD_API_KEY or not ROBINHOOD_PRIVATE_KEY:
        raise RobinhoodAPIError(
            "Robinhood API credentials not configured. "
            "Set ROBINHOOD_API_KEY and ROBINHOOD_PRIVATE_KEY in .env"
        )
    
    # Generate signature
    timestamp = int(time.time())
    signature = _generate_signature(
        api_key=ROBINHOOD_API_KEY,
        private_key_base64=ROBINHOOD_PRIVATE_KEY,
        path=path,
        method=method,
        body=body,
        timestamp=timestamp
    )
    
    # Prepare headers
    headers = {
        "x-api-key": ROBINHOOD_API_KEY,
        "x-signature": signature,
        "x-timestamp": str(timestamp),
        "Content-Type": "application/json"
    }
    
    # Make request
    url = f"{ROBINHOOD_API_BASE}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=body, params=params, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=body, params=params, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=timeout)
        else:
            raise RobinhoodAPIError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response
    
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise RobinhoodAPIError(f"API request failed: {e}")


def get_auth_url() -> str:
    """
    Generate Robinhood OAuth authorization URL for user login.
    
    Returns:
        Authorization URL to redirect user to
    """
    if not ROBINHOOD_CLIENT_ID:
        raise RobinhoodAuthError("ROBINHOOD_CLIENT_ID not set in environment")
    
    params = {
        "client_id": ROBINHOOD_CLIENT_ID,
        "redirect_uri": ROBINHOOD_REDIRECT_URI,
        "response_type": "code",
        "scope": "read write"
    }
    
    url = f"{ROBINHOOD_AUTH_URL}?"
    url += "&".join([f"{k}={v}" for k, v in params.items()])
    
    return url


def exchange_code_for_token(auth_code: str) -> Dict:
    """
    Exchange authorization code for access token.
    
    Args:
        auth_code: Authorization code from OAuth callback
        
    Returns:
        Token response with access_token, refresh_token, expires_in
        
    Raises:
        RobinhoodAuthError: If token exchange fails
    """
    if not ROBINHOOD_CLIENT_ID or not ROBINHOOD_CLIENT_SECRET:
        raise RobinhoodAuthError("Robinhood credentials not configured")
    
    payload = {
        "client_id": ROBINHOOD_CLIENT_ID,
        "client_secret": ROBINHOOD_CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": ROBINHOOD_REDIRECT_URI,
        "scope": "read write"
    }
    
    try:
        response = requests.post(ROBINHOOD_TOKEN_URL, data=payload, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Add expiration timestamp
        if "expires_in" in token_data:
            token_data["expires_at"] = (
                datetime.now() + timedelta(seconds=token_data["expires_in"])
            ).isoformat()
        
        # Save token to file
        _save_token(token_data)
        
        logger.info("Successfully obtained Robinhood access token")
        return token_data
    
    except requests.RequestException as e:
        logger.error(f"Token exchange failed: {e}")
        raise RobinhoodAuthError(f"Failed to exchange code for token: {e}")


def refresh_access_token(refresh_token: Optional[str] = None) -> Dict:
    """
    Refresh Robinhood access token using refresh token.
    
    Args:
        refresh_token: Refresh token (uses saved token if not provided)
        
    Returns:
        New token response
        
    Raises:
        RobinhoodAuthError: If refresh fails
    """
    if not ROBINHOOD_CLIENT_ID or not ROBINHOOD_CLIENT_SECRET:
        raise RobinhoodAuthError("Robinhood credentials not configured")
    
    if not refresh_token:
        token_data = _load_token()
        if not token_data or "refresh_token" not in token_data:
            raise RobinhoodAuthError("No refresh token available")
        refresh_token = token_data["refresh_token"]
    
    payload = {
        "client_id": ROBINHOOD_CLIENT_ID,
        "client_secret": ROBINHOOD_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "read write"
    }
    
    try:
        response = requests.post(ROBINHOOD_TOKEN_URL, data=payload, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Add expiration timestamp
        if "expires_in" in token_data:
            token_data["expires_at"] = (
                datetime.now() + timedelta(seconds=token_data["expires_in"])
            ).isoformat()
        
        # Save updated token
        _save_token(token_data)
        
        logger.info("Successfully refreshed Robinhood access token")
        return token_data
    
    except requests.RequestException as e:
        logger.error(f"Token refresh failed: {e}")
        raise RobinhoodAuthError(f"Failed to refresh token: {e}")


def get_valid_token() -> Optional[str]:
    """
    Get a valid access token, refreshing if needed.
    
    Returns:
        Valid access token or None if not available
    """
    token_data = _load_token()
    
    if not token_data or "access_token" not in token_data:
        logger.warning("No saved token found")
        return None
    
    # Check if token is expired
    if "expires_at" in token_data:
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() > expires_at:
            logger.info("Token expired, refreshing...")
            try:
                token_data = refresh_access_token()
            except RobinhoodAuthError as e:
                logger.error(f"Could not refresh token: {e}")
                return None
    
    return token_data.get("access_token")


def make_request(method: str, endpoint: str, **kwargs) -> Dict:
    """
    Make authenticated request to Robinhood API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., '/account')
        **kwargs: Additional request parameters
        
    Returns:
        JSON response
        
    Raises:
        RobinhoodAPIError: If request fails
    """
    token = get_valid_token()
    if not token:
        raise RobinhoodAPIError("No valid authentication token available")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        **kwargs.pop("headers", {})
    }
    
    url = f"{ROBINHOOD_API_BASE}{endpoint}"
    
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=10,
            **kwargs
        )
        
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException as e:
        logger.error(f"Robinhood API request failed: {e}")
        raise RobinhoodAPIError(f"API request failed: {e}")


def get_account_info() -> Dict:
    """
    Get authenticated user's account information.
    
    Returns:
        Account data (account ID, type, etc.)
    """
    return make_request("GET", "/account/accounts/")


def get_holdings() -> List[Dict]:
    """
    Get user's current cryptocurrency holdings.
    
    Returns:
        List of holdings with symbol, quantity, price, etc.
    """
    try:
        response = make_request("GET", "/account/positions/")
        return response.get("results", [])
    except RobinhoodAPIError as e:
        logger.error(f"Failed to get holdings: {e}")
        return []


def get_crypto_quote(symbol: str) -> Optional[Dict]:
    """
    Get current price quote for cryptocurrency.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH')
        
    Returns:
        Quote data with price, bid, ask, etc.
    """
    try:
        response = make_request(
            "GET",
            f"/marketdata/quotes/crypto/{symbol}/"
        )
        return response
    except RobinhoodAPIError as e:
        logger.error(f"Failed to get quote for {symbol}: {e}")
        return None


def place_order(
    symbol: str,
    quantity: float,
    side: str,  # 'buy' or 'sell'
    price: Optional[float] = None,  # None for market order
    time_in_force: str = "gfd"  # gfd=day, gtc=good til canceled, etc.
) -> Dict:
    """
    Place a cryptocurrency order.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH')
        quantity: Quantity to buy/sell
        side: 'buy' or 'sell'
        price: Limit price (None for market order)
        time_in_force: Order time constraint
        
    Returns:
        Order confirmation with order ID
    """
    if side not in ["buy", "sell"]:
        raise ValueError("side must be 'buy' or 'sell'")
    
    payload = {
        "account_id": _get_account_id(),
        "quantity": quantity,
        "side": side,
        "symbol": symbol.upper(),
        "type": "limit" if price else "market",
        "time_in_force": time_in_force
    }
    
    if price:
        payload["price"] = price
    
    try:
        response = make_request(
            "POST",
            "/orders/",
            json=payload
        )
        logger.info(f"Order placed: {response.get('id')}")
        return response
    except RobinhoodAPIError as e:
        logger.error(f"Failed to place order: {e}")
        raise


def cancel_order(order_id: str) -> bool:
    """
    Cancel an open order.
    
    Args:
        order_id: Order ID to cancel
        
    Returns:
        True if successful
    """
    try:
        make_request("POST", f"/orders/{order_id}/cancel/")
        logger.info(f"Order {order_id} cancelled")
        return True
    except RobinhoodAPIError as e:
        logger.error(f"Failed to cancel order: {e}")
        return False


def get_orders(limit: int = 20) -> List[Dict]:
    """
    Get list of recent orders.
    
    Args:
        limit: Maximum number of orders to retrieve
        
    Returns:
        List of orders
    """
    try:
        response = make_request(
            "GET",
            "/orders/",
            params={"limit": limit}
        )
        return response.get("results", [])
    except RobinhoodAPIError as e:
        logger.error(f"Failed to get orders: {e}")
        return []


# ============================================================================
# Private Helper Functions
# ============================================================================

def _save_token(token_data: Dict) -> None:
    """Save token to local file."""
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)
        logger.debug(f"Token saved to {TOKEN_FILE}")
    except Exception as e:
        logger.error(f"Failed to save token: {e}")


def _load_token() -> Optional[Dict]:
    """Load token from local file."""
    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load token: {e}")
    return None


def _get_account_id() -> str:
    """Get authenticated account ID."""
    try:
        token_data = _load_token()
        if token_data and "account_id" in token_data:
            return token_data["account_id"]
        
        # Fetch from API if not cached
        account_info = get_account_info()
        if account_info and "results" in account_info:
            account_id = account_info["results"][0]["id"]
            # Save to token file
            token_data = _load_token() or {}
            token_data["account_id"] = account_id
            _save_token(token_data)
            return account_id
    except Exception as e:
        logger.error(f"Failed to get account ID: {e}")
    
    raise RobinhoodAPIError("Could not retrieve account ID")


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return get_valid_token() is not None
