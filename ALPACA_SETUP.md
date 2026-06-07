# Alpaca API Integration Guide

## Overview
Your CryptoAI backend now supports **live crypto trading on Alpaca** through their REST API. This allows you to:
- Check account balances and buying power
- View your current holdings
- Get real-time crypto quotes
- Place buy/sell orders (market or limit)
- Manage open orders
- Track order status

## Prerequisites
- Alpaca account (free, supports crypto trading)
- Alpaca API credentials
- Backend running on localhost:8000

## Step 1: Create an Alpaca Account

1. Go to https://alpaca.markets/
2. Click **"Sign Up"** (or **"Get Started"**)
3. Complete the registration process
4. Verify your email

## Step 2: Get API Credentials

### From Alpaca Dashboard:
1. Log in to your Alpaca account: https://app.alpaca.markets/
2. Navigate to **Account** or **API Keys** section (usually in top menu)
3. Click **"Create New Key"** or **"View Keys"**
4. You'll see:
   - **API Key** (starts with `PK...`)
   - **Secret Key** (keep this private!)
5. Copy both values (save them securely)

### Paper Trading vs. Live Trading:
- **Paper Trading** (Default): Test your bot with fake money (no real trades)
  - Base URL: `https://paper-api.alpaca.markets`
  - Great for testing!
- **Live Trading**: Real money trading
  - Base URL: `https://api.alpaca.markets`
  - Requires account funding

## Step 3: Configure Environment Variables

### Create or edit `.env` file in project root:

```
# Alpaca Configuration
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_API_BASE_URL=https://paper-api.alpaca.markets
ALPACA_USE_PAPER=true
```

### Example `.env`:
```
ALPACA_API_KEY=PK1a2b3c4d5e6f7g8h9i0
ALPACA_SECRET_KEY=abc123def456ghi789jkl012mno
ALPACA_API_BASE_URL=https://paper-api.alpaca.markets
ALPACA_USE_PAPER=true
```

## Step 4: Install Dependencies

No extra Alpaca SDK is required. The backend now calls Alpaca HTTP APIs directly.

Install project dependencies as usual:

```bash
pip install -r requirements.txt
```

## Step 5: Verify Setup

1. Start your backend:
```bash
python backend/main.py
```

2. Test the API endpoint:
```bash
curl http://localhost:8000/alpaca/account
```

You should see your account information returned as JSON.

## Common Crypto Symbols on Alpaca

Alpaca supports crypto trading with symbols like:
- `BTC/USD` - Bitcoin
- `ETH/USD` - Ethereum
- `DOGE/USD` - Dogecoin
- `SOL/USD` - Solana
- And many more...

## API Endpoints Available

Your backend now exposes these endpoints:

- `GET /alpaca/account` - Get account info
- `GET /alpaca/holdings` - Get open positions
- `GET /alpaca/quote/{symbol}` - Get crypto quote
- `POST /alpaca/order` - Place an order
- `GET /alpaca/orders` - Get all orders
- `DELETE /alpaca/order/{order_id}` - Cancel an order

## Troubleshooting

### "Missing Alpaca credentials" error
- Make sure `.env` file exists in project root
- Verify `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are set
- Check for typos in environment variable names

### "Connection refused" error
- Verify your API key and secret are correct
- Check internet connection
- Ensure you're using the correct API base URL

### "Insufficient buying power" error
- You don't have enough cash to place the order
- For paper trading, you start with $100,000 in virtual cash
- For live trading, deposit funds to your account

### Cannot place crypto orders
- Make sure the symbol format includes `/USD` (e.g., `BTC/USD`)
- Not all crypto symbols are available - check Alpaca's supported list
- Ensure crypto trading is enabled on your account

## Switching Between Paper and Live Trading

In `.env`, change:
```
# For paper trading:
ALPACA_API_BASE_URL=https://paper-api.alpaca.markets
ALPACA_USE_PAPER=true

# For live trading:
ALPACA_API_BASE_URL=https://api.alpaca.markets
ALPACA_USE_PAPER=false
```

**Warning**: Live trading uses real money. Be careful!

## Security Best Practices

1. **Never commit `.env` to version control** - it contains secrets
2. **Use `.gitignore` to exclude `.env`** - already done in most projects
3. **Rotate API keys periodically**
4. **Use paper trading for testing**
5. **Start with small orders** when switching to live trading

## Support

- Alpaca Documentation: https://docs.alpaca.markets/
- Alpaca Community: https://forum.alpaca.markets/
- Email: support@alpaca.markets
