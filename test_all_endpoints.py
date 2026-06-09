"""Pytest integration checks for core data endpoints."""

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
def test_data_sources_status_endpoint():
    _ensure_backend_available()

    response = requests.get(f"{API_BASE}/api/data-sources/status", timeout=10)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("sources"), dict)


@pytest.mark.integration
def test_coingecko_endpoint_returns_requested_cryptos():
    _ensure_backend_available()

    response = requests.get(
        f"{API_BASE}/api/data/coingecko?crypto_ids=bitcoin,ethereum",
        timeout=15,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("data"), dict)
    assert "bitcoin" in payload["data"]


@pytest.mark.integration
def test_yahoo_finance_endpoint_returns_time_series():
    _ensure_backend_available()

    response = requests.get(
        f"{API_BASE}/api/data/yahoo-finance?symbol=AAPL&period=1y",
        timeout=20,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("symbol") == "AAPL"
    assert isinstance(payload.get("data"), list)
