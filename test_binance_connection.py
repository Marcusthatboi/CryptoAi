"""Pytest integration check for Binance account connectivity."""

import os

import pytest
from dotenv import load_dotenv

from backend.binance_api import BinanceError, get_account_info


@pytest.mark.integration
def test_binance_account_connection():
    """Validate Binance account access when API credentials are configured."""
    load_dotenv(override=False)

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        pytest.skip("BINANCE_API_KEY and BINANCE_API_SECRET are not configured")

    try:
        status = get_account_info()
    except BinanceError as exc:
        pytest.fail(f"Binance API connection failed: {exc}")

    assert isinstance(status.get("balances"), list), "Expected balances list from Binance"
    assert "can_trade" in status, "Expected can_trade key in Binance account response"
