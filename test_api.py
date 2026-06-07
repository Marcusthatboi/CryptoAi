import requests
import json

# Test Yahoo Finance endpoint
r = requests.get('http://localhost:8000/api/data/yahoo-finance?symbol=AAPL&period=1y')
result = r.json()

print(f"Status: {r.status_code}")
print(f"Records: {result.get('count')}")

if result.get('data') and len(result.get('data')) > 0:
    print(f"✅ First record: {json.dumps(result['data'][0], indent=2)}")
    print(f"\n✅ Last record: {json.dumps(result['data'][-1], indent=2)}")
else:
    print("❌ No data returned")
    print(f"Response: {json.dumps(result, indent=2)}")
