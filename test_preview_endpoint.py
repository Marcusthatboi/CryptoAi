"""Pytest integration check for preview endpoint authentication behavior."""

import pytest
import requests


API_BASE = "http://127.0.0.1:8002"


def _ensure_backend_available() -> None:
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        pytest.skip(f"Backend not reachable at {API_BASE}: {exc}")


@pytest.mark.integration
def test_preview():
    _ensure_backend_available()

    # Without auth token, endpoint should reject with auth or premium gating status.
    response = requests.post(
        f"{API_BASE}/api/auto-trading/preview",
        json={
            "symbol": "BTCUSDT",
            "action": "BUY",
            "quantity": 0.001,
            "stop_loss": 59000,
            "take_profit": 65000,
            "acknowledge_risks": True,
            "acknowledge_losses": True,
            "acknowledge_ai_failures": True,
        },
        timeout=10,
    )

    assert response.status_code in {401, 403}, (
        f"Expected protected preview endpoint status 401/403, got {response.status_code}: {response.text[:300]}"
    )
