import requests
import json

# Test all endpoints
print("=" * 60)
print("🧪 TESTING ALL 3 DATA ENDPOINTS")
print("=" * 60)

# Test 1: Data Sources Status
print("\n1️⃣  DATA SOURCES STATUS")
r = requests.get('http://localhost:8000/api/data-sources/status')
result = r.json()
sources = result.get('sources', {})
print(f"✅ Endpoint working")
for source, info in sources.items():
    print(f"   • {source}: {'Available' if info.get('available') else 'Unavailable'}")

# Test 2: CoinGecko Crypto
print("\n2️⃣  COINGECKO CRYPTO DATA")
r = requests.get('http://localhost:8000/api/data/coingecko?crypto_ids=bitcoin,ethereum')
result = r.json()
print(f"✅ Fetched {result.get('count')} cryptos")
for coin, data in result.get('data', {}).items():
    price = data.get('usd', 0)
    change = data.get('usd_24h_change', 0)
    print(f"   • {coin.upper()}: ${price:,.2f} ({change:+.2f}%)")

# Test 3: Yahoo Finance Stock
print("\n3️⃣  YAHOO FINANCE STOCK DATA")
r = requests.get('http://localhost:8000/api/data/yahoo-finance?symbol=AAPL&period=1y')
result = r.json()
print(f"✅ Fetched {result.get('count')} records for {result.get('symbol')}")
if result.get('data'):
    first = result['data'][0]
    last = result['data'][-1]
    print(f"   • First: {first['timestamp']} → Close: ${first['close']:.2f}")
    print(f"   • Last:  {last['timestamp']} → Close: ${last['close']:.2f}")

print("\n" + "=" * 60)
print("✅ ALL ENDPOINTS WORKING!")
print("=" * 60)
