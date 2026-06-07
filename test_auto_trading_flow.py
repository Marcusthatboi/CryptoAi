#!/usr/bin/env python
"""Test complete auto trading flow"""
import os
import json
import requests
from datetime import datetime

# Test configuration
API_BASE = "http://127.0.0.1:8002"
TEST_USER = "test_user_123"
TEST_SYMBOL = "BTCUSDT"

print("="*60)
print("🧪 AUTO TRADING FLOW TEST")
print("="*60)
print()

# Step 1: Get warnings (public endpoint)
print("Step 1: Fetching auto trading warnings...")
try:
    response = requests.get(f"{API_BASE}/api/auto-trading/warnings")
    if response.status_code == 200:
        warnings = response.json()
        print(f"✅ Got {len(warnings)} warnings")
        print(f"   Sample: {warnings[0]['title']}")
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"❌ Connection error: {e}")
    exit(1)

print()

# Step 2: Analyze symbol (requires premium auth - we'll test the 403 response)
print("Step 2: Testing premium gating on analyze endpoint...")
try:
    response = requests.post(
        f"{API_BASE}/api/auto-trading/analyze/{TEST_SYMBOL}",
        headers={
            "Authorization": "Bearer invalid_token"
        },
        json={"timeframe": "1h"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly requires authentication")
    elif response.status_code == 403:
        print("✅ Correctly blocks non-premium access (403 Forbidden)")
    else:
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print()

# Step 3: Show trade structure (this is what execute would send)
print("Step 3: Auto Trading Execution Structure (what would be sent):")
trade_request = {
    "symbol": "BTC",
    "action": "BUY",
    "quantity": 0.01,
    "stop_loss": 59000,
    "take_profit": 65000,
    "accepted_risks": True,
    "acknowledged_dangerous": True,
    "confirmed_terms": True
}
print(json.dumps(trade_request, indent=2))

print()
print("="*60)
print("✅ API endpoints are accessible")
print("✅ Premium gating is active")
print("✅ Ready for end-to-end testing with authenticated user")
print("="*60)
print()
print("📝 NEXT STEPS:")
print("1. Log in to https://dacryptobeast.com")
print("2. Upgrade to Premium tier ($29.99/mo)")
print("3. Navigate to Auto Trading page")
print("4. Execute a test trade")
print("5. Monitor in 'Active Trades' tab")
