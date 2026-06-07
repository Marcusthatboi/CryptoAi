import requests
import json

# Login
login_resp = requests.post('http://localhost:8002/login', json={'username': 'admin', 'password': 'admin'})
login_data = login_resp.json()
if 'access_token' not in login_data:
    print(f"Login failed: {login_data}")
    print(f"Status code: {login_resp.status_code}")
    exit(1)
token = login_data['access_token']

# Get portfolio
portfolio_resp = requests.get('http://localhost:8002/api/portfolio', headers={'Authorization': f'Bearer {token}'})
portfolio = portfolio_resp.json()['portfolio']

# Extract relevant data
holdings = portfolio.get('holdings', [])
realized_pnl = portfolio.get('realized_pnl', {})

print('=== HOLDINGS ===')
for h in holdings:
    qty = float(h.get('quantity', 0) or 0)
    price = float(h.get('price', 0) or 0)
    total = float(h.get('total_value', 0) or 0)
    avg_price = float(h.get('average_price', 0) or 0)
    inv_type = h.get('investment_type', 'unknown')
    print(f"{h['symbol']} ({inv_type}): {qty} units @ ${price} = ${total}")
    print(f"  Average Price: ${avg_price}")

print('\n=== PROFIT SUMMARY ===')
print(f"Realized P&L (Overall): ${realized_pnl.get('overall', 0)}")
print(f"Realized P&L (Fake Money): ${realized_pnl.get('fake_money', 0)}")
print(f"Realized P&L (Real Money): ${realized_pnl.get('real_money', 0)}")

# Manual calculation for fake money
total_cost_basis = 0
total_market_value = 0
for h in holdings:
    if h.get('investment_type') == 'fake_money':
        qty = float(h.get('quantity', 0) or 0)
        avg_price = float(h.get('average_price', h.get('price', 0)) or 0)
        market_val = float(h.get('total_value', 0) or 0)
        
        cost = qty * avg_price
        total_cost_basis += cost
        total_market_value += market_val
        
        print(f"\n{h['symbol']}: Cost={qty}*${avg_price}=${cost:.2f}, Market=${market_val:.2f}")

unrealized_profit = total_market_value - total_cost_basis

print(f"\n=== MANUAL VERIFICATION (FAKE MONEY) ===")
print(f"Total Cost Basis: ${total_cost_basis:.2f}")
print(f"Total Market Value: ${total_market_value:.2f}")
print(f"Unrealized Profit: ${unrealized_profit:.2f}")
if total_cost_basis > 0:
    print(f"Return %: {(unrealized_profit / total_cost_basis * 100):.2f}%")
