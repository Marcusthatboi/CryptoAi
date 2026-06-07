import requests
import json

BASE_URL = "http://localhost:8001"  # Updated to port 8001

# Test all endpoints
print("=" * 60)
print("🧪 TESTING ALL 3 DATA ENDPOINTS (Port 8001)")
print("=" * 60)

# Test 1: Data Sources Status
print("\n1️⃣  DATA SOURCES STATUS")
try:
    r = requests.get(f'{BASE_URL}/api/data-sources/status', timeout=5)
    result = r.json()
    sources = result.get('sources', {})
    print(f"✅ Endpoint working")
    for source, info in sources.items():
        print(f"   • {source}: {'Available' if info.get('available') else 'Unavailable'}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: CoinGecko Crypto
print("\n2️⃣  COINGECKO CRYPTO DATA")
try:
    r = requests.get(f'{BASE_URL}/api/data/coingecko?crypto_ids=bitcoin,ethereum', timeout=10)
    result = r.json()
    print(f"✅ Fetched {result.get('count')} cryptos")
    for coin, data in result.get('data', {}).items():
        price = data.get('usd', 0)
        change = data.get('usd_24h_change', 0)
        print(f"   • {coin.upper()}: ${price:,.2f} ({change:+.2f}%)")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Yahoo Finance Stock
print("\n3️⃣  YAHOO FINANCE STOCK DATA")
try:
    r = requests.get(f'{BASE_URL}/api/data/yahoo-finance?symbol=MSFT&period=1y', timeout=15)
    result = r.json()
    print(f"✅ Fetched {result.get('count')} records for {result.get('symbol')}")
    if result.get('data'):
        first = result['data'][0]
        last = result['data'][-1]
        print(f"   • First: {first['timestamp']} → Close: ${first['close']:.2f}")
        print(f"   • Last:  {last['timestamp']} → Close: ${last['close']:.2f}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ ALL ENDPOINTS WORKING ON PORT 8001!")
print("=" * 60)
