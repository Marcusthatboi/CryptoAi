"""Pytest integration checks for auto trading flow endpoints."""

import pytest
import requests


API_BASE = "http://127.0.0.1:8002"
TEST_SYMBOL = "BTCUSDT"


def _ensure_backend_available() -> None:
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        pytest.skip(f"Backend not reachable at {API_BASE}: {exc}")


@pytest.mark.integration
def test_auto_trading_warnings_endpoint_returns_payload_with_warnings_list():
    _ensure_backend_available()

    response = requests.get(f"{API_BASE}/api/auto-trading/warnings", timeout=10)
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"

    payload = response.json()
    assert isinstance(payload, dict), "Expected warnings endpoint to return an object payload"
    assert payload.get("status") == "ok"
    assert isinstance(payload.get("warnings"), list), "Expected warnings field to be a list"


@pytest.mark.integration
def test_auto_trading_analyze_requires_auth_or_premium():
    _ensure_backend_available()

    response = requests.post(
        f"{API_BASE}/api/auto-trading/analyze/{TEST_SYMBOL}",
        headers={"Authorization": "Bearer invalid_token"},
        json={"timeframe": "1h"},
        timeout=10,
    )

    assert response.status_code in {401, 403}, (
        f"Expected auth/premium gate status 401/403, got {response.status_code}: {response.text[:300]}"
    )
