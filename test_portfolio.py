import requests

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInVzZXJfaWQiOiI2YTFkZWUyNGFiMWFkZWYyMTIzN2M1MzciLCJleHAiOjE3ODA0MzI4MDR9.SKDzxuysiVELdXxzLE1TZE1v3x3_4LCksaj2dzaaQTE'

# Get final portfolio state
portfolio_resp = requests.get(
    'http://localhost:8002/api/user/portfolio',
    headers={'Authorization': f'Bearer {token}'},
    timeout=10
)
data = portfolio_resp.json()

print('=== FINAL PORTFOLIO STATE ===')
print(f'Cash Balance: {data.get("cash", 100000)}')
print(f'Holdings Count: {len(data.get("holdings", []))}')
print('')
print('Holdings:')
for i, h in enumerate(data.get('holdings', []), 1):
    print(f'{i}. {h["symbol"]}: {h["quantity"]} units @ {h["price"]}/unit = {h["total_value"]}')
