"""Pytest integration check for Yahoo Finance endpoint."""

import pytest
import requests


API_BASE = "http://127.0.0.1:8000"


def _ensure_backend_available() -> None:
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        pytest.skip(f"Backend not reachable at {API_BASE}: {exc}")


@pytest.mark.integration
def test_yahoo_finance_endpoint_smoke():
    _ensure_backend_available()

    response = requests.get(
        f"{API_BASE}/api/data/yahoo-finance?symbol=AAPL&period=1y",
        timeout=20,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("symbol") == "AAPL"
    assert isinstance(payload.get("data"), list)
