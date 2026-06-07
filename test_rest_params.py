"""Quick smoke test for direct Alpaca HTTP integration (no SDK dependency)."""

from backend.alpaca_api import get_alpaca_client, is_authenticated

print("Testing direct Alpaca HTTP integration")

try:
    client = get_alpaca_client()
    print("Client config created successfully")
    print(f"Base URL: {client.get('base_url')}")
except Exception as exc:
    print(f"Client initialization error: {exc}")

print(f"Authenticated: {is_authenticated()}")
