# Binance API Integration Guide

## Overview
Your CryptoAI backend now supports **live trading and market data from Binance**, the world's largest crypto exchange. This enables:
- Real-time price quotes for 2000+ cryptocurrencies
- Portfolio tracking and valuation
- Live market data (candlesticks, volume, trends)
- Buy/sell order placement
- Order management and history
- Top gainers/losers tracking

## Why Binance?
✅ **Largest exchange** - Deep liquidity, 2000+ trading pairs  
✅ **Free API** - No rate limits for free tier, generous usage  
✅ **Testnet available** - Practice trading without real money  
✅ **Better data** - More coins than Robinhood  
✅ **Margin trading** - Advanced trading strategies  
✅ **RESTful API** - Simple HTTP-based integration  

## Prerequisites
- Binance account (free signup at https://www.binance.com)
- API credentials (get in account settings)
- Backend running

## Step 1: Create Binance API Keys

### Method A: Mainnet (Real Trading)
1. Go to **Binance Account** → **Settings** → **API Management**
   - URL: https://www.binance.com/en/user/settings/api-management
2. Click **"Create API"**
3. Choose type: **Personal Trading**
4. Label: `CryptoAI Trading Bot`
5. Agree to terms and create
6. **Enable these restrictions:**
   - ✅ Spot trading
   - ✅ Margin trading (optional)
   - ✅ Futures trading (optional)
7. Copy:
   - **API Key**
   - **Secret Key**

### Method B: Testnet (Recommended First!)
1. Go to **Binance Testnet**: https://testnet.binance.vision/
2. This gives you free testnet API keys to practice
3. Same setup as above
4. **Advantages:**
   - Practice without risking real money
   - Same API as production
   - Fresh account with test USDT

## Step 2: Configure Environment

### Create `.env` file (or edit if exists):
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=false  # Set true for testnet
```

Or copy from example:
```powershell
copy .env.example .env
# Edit .env with your credentials
```

**For testnet:**
```
BINANCE_TESTNET=true
```

## Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

This includes `python-binance` (official Binance wrapper).

## Step 4: Start Backend

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

## Step 5: Test Connection

Go to: **http://localhost:8000/docs**

Find: **GET /api/binance/status**
- Click "Try it out"
- Should return `"connected": true`

## API Endpoints

### Connection & Account

**Check Connection**
```
GET /api/binance/status
```
Response:
```json
{
  "connected": true,
  "message": "Connected to Binance API",
  "timestamp": "2024-01-15T10:00:00"
}
```

---

**Get Account Info**
```
GET /api/binance/account
```
Returns trading status and commission rates.

---

### Balances & Portfolio

**Get Single Balance**
```
GET /api/binance/balance?asset=BTC
```
Response:
```json
{
  "asset": "BTC",
  "free": 0.5,
  "locked": 0.1,
  "total": 0.6
}
```

---

**Get All Balances**
```
GET /api/binance/balance
```
Returns all non-zero balances (sorted by value).

---

**Get Portfolio Value**
```
GET /api/binance/portfolio?base_currency=USDT
```
Response:
```json
{
  "total_value": 50000.00,
  "base_currency": "USDT",
  "holdings": [
    {
      "asset": "BTC",
      "quantity": 0.5,
      "price": 42000.00,
      "value": 21000.00,
      "percentage": 42.0
    }
  ],
  "updated_at": "2024-01-15T10:00:00"
}
```

---

### Market Data

**Get Ticker (24hr stats)**
```
GET /api/binance/ticker/BTCUSDT
```
Response:
```json
{
  "symbol": "BTCUSDT",
  "price": 42505.00,
  "bid": 42500.00,
  "ask": 42510.00,
  "high_24h": 43000.00,
  "low_24h": 41000.00,
  "volume": 15000.5,
  "quote_volume": 631500250.00,
  "price_change": 500.00,
  "price_change_percent": 1.19,
  "timestamp": "2024-01-15T10:00:00"
}
```

---

**Get Candlesticks (OHLCV)**
```
GET /api/binance/klines/BTCUSDT?interval=1h&limit=24
```

**Parameters:**
- `interval`: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
- `limit`: 1-1000 (default: 100)

Response:
```json
[
  {
    "open_time": "2024-01-15T09:00:00",
    "open": 42000.00,
    "high": 42500.00,
    "low": 41900.00,
    "close": 42400.00,
    "volume": 500.5,
    "close_time": "2024-01-15T10:00:00",
    "quote_volume": 21170000.00
  }
]
```

---

**Get Top Gainers**
```
GET /api/binance/gainers?limit=10
```
Returns top 10 gainers in last 24 hours.

---

### Trading

**Get Trading Pairs**
```
GET /api/binance/trading-pairs?quote_asset=USDT&limit=100
```

---

**Search Symbol**
```
GET /api/binance/search/BTC
```

---

**Place Order**
```
POST /api/binance/trade
```

Request body:
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "LIMIT",
  "quantity": 0.1,
  "price": 42000.00,
  "time_in_force": "GTC"
}
```

**Parameters:**
- `side`: "BUY" or "SELL"
- `order_type`: "LIMIT" or "MARKET"
- `price`: Required for LIMIT, omit for MARKET
- `time_in_force`: "GTC" (good-til-cancel), "IOC", "FOK", etc.

Response:
```json
{
  "success": true,
  "order_id": 123456789,
  "message": "Order placed: BUY 0.1 BTCUSDT",
  "timestamp": "2024-01-15T10:00:00"
}
```

---

**Cancel Order**
```
POST /api/binance/cancel-order?symbol=BTCUSDT&order_id=123456789
```

---

**Get Order Status**
```
GET /api/binance/order-status?symbol=BTCUSDT&order_id=123456789
```

---

**Get Open Orders**
```
GET /api/binance/open-orders
```
Or filter by symbol:
```
GET /api/binance/open-orders?symbol=BTCUSDT
```

---

**Get Order History**
```
GET /api/binance/order-history?limit=20
```

Response:
```json
[
  {
    "order_id": 123456789,
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": 0.1,
    "executed_quantity": 0.1,
    "price": 42000.00,
    "status": "FILLED",
    "timestamp": "2024-01-15T10:00:00",
    "update_time": "2024-01-15T10:00:15"
  }
]
```

---

## Testing Workflow

### 1. Check Connection
```
GET /api/binance/status
```

### 2. Check Account
```
GET /api/binance/account
```

### 3. View Portfolio
```
GET /api/binance/portfolio
```

### 4. Get Price Data
```
GET /api/binance/ticker/BTCUSDT
```

### 5. Get Historical Data
```
GET /api/binance/klines/BTCUSDT?interval=1h&limit=24
```

### 6. Place Test Order (on testnet!)
```
POST /api/binance/trade
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "LIMIT",
  "quantity": 0.001,
  "price": 40000.00
}
```

### 7. Check Open Orders
```
GET /api/binance/open-orders
```

### 8. Cancel Test Order
```
POST /api/binance/cancel-order?symbol=BTCUSDT&order_id=YOUR_ORDER_ID
```

---

## Security Best Practices

⚠️ **IMPORTANT:**

1. **API Key Restrictions:**
   - Restrict to "Spot Trading" only (disable withdrawal)
   - Restrict to your IP address (if available)
   - Set trading limits

2. **Secrets:**
   - Never commit `.env` to git
   - Never share API key/secret
   - Store in `.env` (added to `.gitignore`)

3. **Testnet First:**
   - Always test on testnet before mainnet
   - Verify all orders work correctly
   - No financial risk on testnet

4. **Rate Limits:**
   - Binance has rate limits (1200 requests/minute)
   - Cache prices when possible
   - Add delays for burst requests

5. **Order Safety:**
   - Always verify orders before placing
   - Use limit orders, not market orders
   - Start with small quantities

---

## Troubleshooting

### "Binance credentials not configured"
- Check `.env` file exists in project root
- Verify API key and secret are correct
- Restart backend after creating `.env`

### "Connection failed"
- Check Binance API is accessible
- Try API ping: `GET /api/binance/status`
- Check firewall/VPN not blocking API

### "Invalid API Key"
- Verify you copied key correctly (no spaces)
- Check key hasn't been deleted in Binance console
- Try regenerating key

### "Order failed: Insufficient balance"
- Check balance: `GET /api/binance/balance`
- Ensure quantity is available
- Check for locked funds

### "Symbol not found"
- Verify symbol format (e.g., "BTCUSDT" not "BTC")
- Check symbol exists: `GET /api/binance/trading-pairs`
- Use `GET /api/binance/search/BTC` to find

---

## Integration with Chat AI

Your Ollama AI can now answer trading questions:
- "What's the price of Bitcoin?"
- "Show me my portfolio"
- "Get candlestick data for Ethereum"
- "What are the top gainers?"
- "Buy 0.5 Bitcoin at $42,000"

Just ask in the chat!

---

## Next Steps

1. ✅ Create Binance API keys
2. ✅ Configure `.env` file
3. ✅ Install dependencies (`pip install -r requirements.txt`)
4. ✅ Start backend
5. ✅ Test with `/api/binance/status`
6. ✅ Get balances and portfolio
7. ✅ Try market data endpoints
8. ✅ Place test orders (on testnet!)
9. 🎉 Live trading!

---

## Useful Links

- **Binance API Docs:** https://binance-docs.github.io/apidocs/
- **Python Binance:** https://github.com/sammchardy/python-binance
- **Binance Testnet:** https://testnet.binance.vision/
- **Trading Pairs:** https://www.binance.com/en/trade
- **24hr Stats:** https://www.binance.com/en/statistics

---

Enjoy your Binance integration! Start with testnet, then go live. 🚀
