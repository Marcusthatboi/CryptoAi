#!/usr/bin/env python3
"""
Test Alpaca Trading API Connection
===================================
Tests the Trading API credentials with Legacy authentication.
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("ALPACA TRADING API CONNECTION TEST")
print("=" * 60)

# Get credentials
api_key_id = os.getenv("ALPACA_API_KEY")
api_secret_key = os.getenv("ALPACA_SECRET_KEY")
base_url = os.getenv("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets")

print("\n1. Checking credentials...")
print(f"   API Key ID present: {bool(api_key_id)}")
if api_key_id:
    print(f"   API Key ID preview: {api_key_id[:15]}...")
print(f"   API Secret present: {bool(api_secret_key)}")
if api_secret_key:
    print(f"   API Secret preview: {api_secret_key[:15]}...")
print(f"   Base URL: {base_url}")

if not api_key_id or not api_secret_key:
    print("\n❌ ERROR: Missing credentials in .env file")
    sys.exit(1)

# Test direct API call
print("\n2. Testing Trading API with Legacy authentication...")

url = f"{base_url}/v2/account"
headers = {
    "APCA-API-KEY-ID": api_key_id,
    "APCA-API-SECRET-KEY": api_secret_key,
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        print(f"   ✅ SUCCESS (Status: {response.status_code})")
        account_data = response.json()
        print("\n3. Account Information:")
        print(f"   Account ID: {account_data.get('id')}")
        print(f"   Account Status: {account_data.get('status')}")
        print(f"   Crypto Status: {account_data.get('crypto_status')}")
        print(f"   Buying Power: ${account_data.get('buying_power')}")
        print(f"   Account Number: {account_data.get('account_number')}")
        print(f"   Account Type: {account_data.get('account_type', 'N/A')}")
        print(f"   Options Trading Level: {account_data.get('options_trading_level')}")
        print("\n✅ AUTHENTICATION SUCCESSFUL - Ready to trade!")
        sys.exit(0)
    else:
        print(f"   ❌ ERROR: Status {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
        
except requests.RequestException as e:
    print(f"   ❌ ERROR: {str(e)}")
    sys.exit(1)

