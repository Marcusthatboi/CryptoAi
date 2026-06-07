# Robinhood API Integration Guide

## Overview
Your CryptoAI backend now supports **live trading on Robinhood** through their OAuth 2.0 API. This allows you to:
- Check account balances and holdings
- View real-time crypto quotes
- Place buy/sell orders
- Manage open orders

## Prerequisites
- Robinhood account (with crypto trading enabled)
- Robinhood API credentials
- Backend running on localhost:8000

## Step 1: Get Robinhood API Credentials

### Method A: Robinhood Developer Portal (Recommended)
1. Go to your Robinhood account: https://robinhood.com/us/en/
2. Navigate to **Account Settings** → **Developer** (or **API**)
3. Click **"Create Application"**
4. Fill in the form:
   - **App Name**: CryptoAI Trading Bot
   - **App Type**: Personal
   - **Redirect URI**: `http://localhost:8000/auth/robinhood/callback`
5. Accept terms and create
6. You'll receive:
   - **Client ID**
   - **Client Secret**
   - Keep these safe!

### Method B: Robinhood CLI (if available)
```bash
robinhood auth setup
```

## Step 2: Configure Environment Variables

### Create `.env` file in project root:
```
ROBINHOOD_CLIENT_ID=your_client_id_here
ROBINHOOD_CLIENT_SECRET=your_client_secret_here
ROBINHOOD_REDIRECT_URI=http://localhost:8000/auth/robinhood/callback
```

Or copy and edit `.env.example`:
```powershell
Copy-Item .env.example .env
# Edit .env with your credentials
```

## Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

This includes `python-dotenv` for environment variable management.

## Step 4: Start Backend

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

## Step 5: Authenticate

### Option A: API Documentation (Easy)
1. Go to: `http://localhost:8000/docs`
2. Find **GET /api/robinhood/auth-status**
3. Click "Try it out"
4. Copy the `auth_url` from response
5. Open auth_url in browser
6. Log in to Robinhood and authorize the app
7. You'll be redirected to the callback URL

### Option B: Direct Link
In browser, go to the auth URL returned by:
```
GET http://localhost:8000/api/robinhood/auth-status
```

## API Endpoints

### Authentication
```
GET /api/robinhood/auth-status
```
Check if authenticated and get login URL if needed.

**Response:**
```json
{
  "authenticated": false,
  "auth_url": "https://api.robinhood.com/oauth2/authorize?...",
  "message": "Not authenticated. Visit the auth_url to login."
}
```

---

### Account Information
```
GET /api/robinhood/account
```
Get account details, buying power, etc.

**Response:**
```json
{
  "id": "account-id",
  "account_type": "margin",
  "buying_power": 10000.50,
  "cash": 5000.00,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Holdings
```
GET /api/robinhood/holdings
```
Get current cryptocurrency holdings.

**Response:**
```json
[
  {
    "symbol": "BTC",
    "quantity": 0.5,
    "current_value": 21000.00,
    "cost_basis": 20000.00,
    "percent_change": 5.0
  },
  {
    "symbol": "ETH",
    "quantity": 10.5,
    "current_value": 21000.00,
    "cost_basis": 20000.00,
    "percent_change": 5.0
  }
]
```

---

### Get Quote
```
GET /api/robinhood/quote/{symbol}
```
Get current price for a cryptocurrency.

**Example:**
```
GET /api/robinhood/quote/BTC
```

**Response:**
```json
{
  "symbol": "BTC",
  "bid_price": "42500.00",
  "ask_price": "42510.00",
  "last_price": "42505.00",
  "bid_size": "1.5",
  "ask_size": "2.0"
}
```

---

### Place Order (Trade)
```
POST /api/robinhood/trade
```
Place a buy or sell order.

**Request Body:**
```json
{
  "symbol": "BTC",
  "quantity": 0.5,
  "side": "buy",
  "price": 42500.00,
  "time_in_force": "gfd"
}
```

**Parameters:**
- `symbol`: BTC, ETH, DOGE, etc.
- `quantity`: Amount to buy/sell
- `side`: "buy" or "sell"
- `price`: (Optional) Limit price. Omit for market order
- `time_in_force`: "gfd" (day), "gtc" (good til canceled), etc.

**Response:**
```json
{
  "success": true,
  "order_id": "order-uuid",
  "message": "Order placed: BUY 0.5 BTC",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Cancel Order
```
POST /api/robinhood/cancel-order/{order_id}
```
Cancel an open order.

**Response:**
```json
{
  "success": true,
  "message": "Order order-uuid cancelled",
  "order_id": "order-uuid"
}
```

---

### Get Orders
```
GET /api/robinhood/orders?limit=20
```
Get recent orders.

**Response:**
```json
[
  {
    "id": "order-uuid",
    "symbol": "BTC",
    "side": "buy",
    "quantity": 0.5,
    "price": 42500.00,
    "status": "filled",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:30Z"
  }
]
```

---

## Testing in API Docs

1. Go to `http://localhost:8000/docs`
2. Find any Robinhood endpoint
3. Click "Try it out"
4. Fill in parameters (if needed)
5. Click "Execute"
6. View response

## Example: Buy Bitcoin

1. **Authenticate first** (see Step 5)
2. **Check account:**
   ```
   GET /api/robinhood/account
   ```
   Get your account ID and verify buying power

3. **Check holdings:**
   ```
   GET /api/robinhood/holdings
   ```

4. **Get current quote:**
   ```
   GET /api/robinhood/quote/BTC
   ```

5. **Place order:**
   ```
   POST /api/robinhood/trade
   {
     "symbol": "BTC",
     "quantity": 0.1,
     "side": "buy",
     "price": 42500.00
   }
   ```

6. **Check order status:**
   ```
   GET /api/robinhood/orders
   ```

## Troubleshooting

### "ROBINHOOD_CLIENT_ID not set"
- Check `.env` file exists in project root
- Verify credentials are correct
- Restart backend after creating `.env`

### "Not authenticated"
- Go to `/api/robinhood/auth-status` and follow the auth_url
- Make sure you authorize the app in Robinhood
- Token is saved locally after auth

### "Token expired"
- Backend automatically refreshes tokens
- If error persists, re-authenticate by visiting `/api/robinhood/auth-status`

### CORS Errors
- Frontend CORS is enabled for localhost:3000 and localhost:5173
- If using different port, update `allow_origins` in main.py

### Rate Limiting
- Robinhood has rate limits (typically 120 requests/minute)
- Cache results when possible
- Add delays between rapid requests

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` to git (it's in `.gitignore`)
- Never share `ROBINHOOD_CLIENT_SECRET`
- Keep tokens secure (they're saved in `.robinhood_token.json`)
- Use HTTPS in production
- Add API key rotation regularly

## Integration with Chat AI

Your Ollama AI can now answer trading questions:
- "What's my Bitcoin balance?"
- "Should I buy more Ethereum?" (analyze trends + holdings)
- "Show me my recent orders"
- "Place a buy order for 0.5 BTC at $42,000"

Just ask in the chat interface!

## Next Steps

1. ✅ Get credentials from Robinhood
2. ✅ Create `.env` file
3. ✅ Install dependencies (`pip install -r requirements.txt`)
4. ✅ Start backend
5. ✅ Authenticate via API
6. ✅ Test trading endpoints
7. 🎉 Start trading!

For questions or issues, check the API documentation at `http://localhost:8000/docs` once backend is running.
