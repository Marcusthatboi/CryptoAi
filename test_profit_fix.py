"""Pytest integration checks for portfolio profit-related endpoints."""

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
def test_backend_docs_available_for_profit_checks():
    _ensure_backend_available()


@pytest.mark.integration
def test_portfolio_endpoint_requires_authentication():
    _ensure_backend_available()

    response = requests.get(f"{API_BASE}/api/user/portfolio", timeout=10)
    assert response.status_code in {401, 403}, (
        f"Expected protected portfolio endpoint status 401/403, got {response.status_code}"
    )
