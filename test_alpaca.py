"""Pytest integration check for Alpaca Trading API credentials."""

import os

import pytest
import requests
from dotenv import load_dotenv


@pytest.mark.integration
def test_alpaca_account_connection():
    """Validate Alpaca account endpoint when credentials are configured."""
    load_dotenv(override=False)

    api_key_id = os.getenv("ALPACA_API_KEY")
    api_secret_key = os.getenv("ALPACA_SECRET_KEY")
    base_url = os.getenv("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets").rstrip("/")

    if not api_key_id or not api_secret_key:
        pytest.skip("ALPACA_API_KEY and ALPACA_SECRET_KEY are not configured")

    response = requests.get(
        f"{base_url}/v2/account",
        headers={
            "APCA-API-KEY-ID": api_key_id,
            "APCA-API-SECRET-KEY": api_secret_key,
        },
        timeout=10,
    )

    assert response.status_code == 200, (
        f"Alpaca authentication failed ({response.status_code}): {response.text[:500]}"
    )

    payload = response.json()
    assert payload.get("id"), "Expected account id in Alpaca response"
    assert payload.get("status"), "Expected account status in Alpaca response"

