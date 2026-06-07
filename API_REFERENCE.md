# CryptoAI API Reference

**Base URL**: `http://localhost:8002`

**Authentication**: JWT Bearer token in `Authorization` header (24-hour expiration)

---

## Authentication Endpoints

### POST `/auth/register`
Register a new user account.

**Request**:
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "password123"
}
```

**Response** (201):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "admin"
}
```

**Errors**:
- `400`: Username or email already exists
- `422`: Validation error

---

### POST `/auth/login`
Authenticate and receive JWT token.

**Request**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "admin"
}
```

**Errors**:
- `401`: Invalid credentials
- `422`: Validation error

---

### GET `/auth/profile`
Get authenticated user profile.

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200):
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "portfolio": {
    "cash_balance": 100000.00,
    "investments": [
      {
        "symbol": "BITCOIN",
        "quantity": 0.00220291,
        "purchase_price": 45394.46,
        "amount": 100.00,
        "timestamp": "2026-06-01T20:30:00Z"
      }
    ]
  }
}
```

**Errors**:
- `401`: Invalid or expired token

---

## Data Source Endpoints (NEW)

### GET `/api/data-sources/status`
Check availability and configuration status of all data sources.

**Response** (200):
```json
{
  "coingecko": {
    "available": true,
    "rate_limit": "50 calls/min",
    "cache_duration": 300,
    "description": "Free crypto data provider"
  },
  "yahoo_finance": {
    "available": true,
    "rate_limit": "unlimited",
    "description": "Stock and crypto historical data"
  },
  "alpha_vantage": {
    "available": false,
    "rate_limit": "5 calls/min (demo key)",
    "status": "Demo key limit exceeded"
  },
  "coinmarketcap": {
    "available": false,
    "rate_limit": "333 calls/day",
    "status": "API key not configured"
  },
  "binance": {
    "available": true,
    "description": "Direct Binance API access"
  }
}
```

---

### GET `/api/data/coingecko`
Fetch comprehensive crypto data from CoinGecko.

**Query Parameters**:
- `crypto_ids` (required): Comma-separated crypto IDs (e.g., `bitcoin,ethereum`)
- `vs_currency` (optional): Currency code (default: `usd`)

**Example**: `GET /api/data/coingecko?crypto_ids=bitcoin,ethereum&vs_currency=usd`

**Response** (200):
```json
{
  "bitcoin": {
    "price": 71562.34,
    "market_cap": 1408234567890,
    "market_cap_rank": 1,
    "total_volume": 45678901234,
    "high_24h": 72500,
    "low_24h": 70000,
    "price_change_24h": -1250.50,
    "price_change_24h_percent": -1.72,
    "market_cap_change_24h_percent": -2.1,
    "circulating_supply": 21000000,
    "max_supply": 21000000,
    "ath": 69045,
    "atl": 67.81,
    "ath_change_percent": 3.66,
    "ath_date": "2021-11-10",
    "atl_date": "2013-07-06"
  },
  "ethereum": {
    "price": 2002.44,
    "market_cap": 240567890123,
    "market_cap_rank": 2,
    "total_volume": 12345678901,
    "high_24h": 2050,
    "low_24h": 1950,
    "price_change_24h": 2.11,
    "price_change_24h_percent": 0.11,
    "market_cap_change_24h_percent": 0.08,
    "circulating_supply": 120567890,
    "ath": 4891,
    "atl": 0.311,
    "ath_change_percent": -59.05,
    "ath_date": "2021-11-16",
    "atl_date": "2015-01-14"
  }
}
```

**Errors**:
- `400`: Missing or invalid crypto_ids
- `503`: CoinGecko API unavailable (fallback to cache)
- `429`: Rate limit exceeded

---

### GET `/api/data/yahoo-finance`
Fetch historical OHLCV data for stocks and crypto.

**Query Parameters**:
- `symbol` (required): Stock/crypto symbol (e.g., `AAPL`, `BTC-USD`, `ETH-USD`)
- `period` (optional): Time period (default: `1y`)
  - Valid: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`
- `interval` (optional): Data interval (default: `1d`)
  - Valid: `1m`, `5m`, `15m`, `30m`, `60m`, `1d`, `1wk`, `1mo`

**Example**: `GET /api/data/yahoo-finance?symbol=AAPL&period=1y&interval=1d`

**Response** (200):
```json
{
  "symbol": "AAPL",
  "data": [
    {
      "date": "2025-06-01",
      "open": 182.45,
      "high": 184.12,
      "low": 181.89,
      "close": 183.67,
      "volume": 52341000
    },
    {
      "date": "2025-05-31",
      "open": 181.23,
      "high": 182.99,
      "low": 180.56,
      "close": 182.45,
      "volume": 48923000
    }
  ],
  "record_count": 251,
  "period": "1y",
  "interval": "1d"
}
```

**Errors**:
- `400`: Invalid symbol or period
- `404`: Symbol not found
- `503`: Yahoo Finance unavailable

---

### GET `/api/data/alpha-vantage/stock/{symbol}`
Fetch stock data from Alpha Vantage.

**Path Parameters**:
- `symbol` (required): Stock symbol (e.g., `AAPL`, `MSFT`)

**Query Parameters**:
- `outputsize` (optional): `full` or `compact` (default: `compact` - last 100 records)

**Example**: `GET /api/data/alpha-vantage/stock/AAPL?outputsize=full`

**Response** (200):
```json
{
  "symbol": "AAPL",
  "data": [
    {
      "date": "2025-06-01",
      "open": "182.45",
      "high": "184.12",
      "low": "181.89",
      "close": "183.67",
      "volume": "52341000"
    }
  ],
  "record_count": 100,
  "note": "Alpha Vantage: Limited by 5 calls/min and 500/day on free tier"
}
```

**Rate Limits**:
- Free tier: 5 requests/minute, 500/day
- Demo API key has strict limitations

**Errors**:
- `400`: Invalid symbol
- `429`: Rate limit exceeded
- `503`: Alpha Vantage unavailable

---

### GET `/api/data/alpha-vantage/forex/{from_symbol}/{to_symbol}`
Fetch forex exchange rates.

**Path Parameters**:
- `from_symbol` (required): Source currency (e.g., `USD`)
- `to_symbol` (required): Target currency (e.g., `EUR`)

**Example**: `GET /api/data/alpha-vantage/forex/USD/EUR`

**Response** (200):
```json
{
  "from_symbol": "USD",
  "to_symbol": "EUR",
  "exchange_rate": 0.9245,
  "bid": 0.92445,
  "ask": 0.92455,
  "timestamp": "2026-06-01T15:30:00Z"
}
```

**Errors**:
- `400`: Invalid currency codes
- `429`: Rate limit exceeded

---

### GET `/api/data/coinmarketcap`
Fetch crypto data from CoinMarketCap.

**Query Parameters**:
- `symbols` (required): Comma-separated symbols (e.g., `BTC,ETH,ADA`)
- `limit` (optional): Max results (default: 100, max: 5000)

**Example**: `GET /api/data/coinmarketcap?symbols=BTC,ETH&limit=100`

**Response** (200):
```json
{
  "status": {
    "timestamp": "2026-06-01T15:30:00.000Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 45,
    "credit_count": 1
  },
  "data": {
    "BTC": {
      "id": 1,
      "name": "Bitcoin",
      "symbol": "BTC",
      "slug": "bitcoin",
      "num_market_pairs": 1234,
      "date_added": "2013-04-28T00:00:00.000Z",
      "tags": ["mineable", "pow", "sha-256"],
      "max_supply": 21000000,
      "circulating_supply": 21000000,
      "total_supply": 21000000,
      "platform": null,
      "cmc_rank": 1,
      "last_updated": "2026-06-01T15:30:00.000Z",
      "quote": {
        "USD": {
          "price": 71562.34,
          "volume_24h": 45678901234,
          "volume_change_24h": -2.5,
          "percent_change_1h": -0.5,
          "percent_change_24h": -1.72,
          "percent_change_7d": 3.2,
          "market_cap": 1408234567890,
          "market_cap_dominance": 48.5,
          "fully_diluted_market_cap": 1408234567890,
          "last_updated": "2026-06-01T15:30:00.000Z"
        }
      }
    }
  }
}
```

**Rate Limits**:
- Free tier: 333 calls/day
- Requires API key configured in `.env`

**Errors**:
- `400`: Invalid symbols
- `401`: API key not configured
- `429`: Rate limit exceeded

---

### POST `/api/data/collect`
Trigger background data collection from all sources.

**Request Body**:
```json
{
  "crypto_symbols": ["bitcoin", "ethereum", "cardano"],
  "stock_symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

**Response** (202):
```json
{
  "status": "Collection started",
  "job_id": "collect_2026-06-01_15:30:00",
  "symbols": {
    "crypto": 3,
    "stocks": 3
  },
  "message": "Data collection running in background. Check status with job_id."
}
```

**Errors**:
- `400`: Invalid symbols
- `503`: Collection service unavailable

---

### GET `/api/data/export`
Export collected data to CSV/JSON format.

**Query Parameters**:
- `crypto_id` (optional): Specific crypto to export
- `format` (optional): `csv` or `json` (default: `csv`)

**Example**: `GET /api/data/export?crypto_id=bitcoin&format=csv`

**Response** (200):
```
crypto_id,date,price,market_cap,volume_24h,price_change_24h
bitcoin,2026-06-01,71562.34,1408234567890,45678901234,-1250.50
bitcoin,2026-05-31,72812.84,1412345678901,52341234567,1234.56
...
```

**Errors**:
- `400`: Invalid crypto_id or format
- `404`: No data found for export

---

## Investment Endpoints

### POST `/api/user/portfolio/invest/fake`
Make a fake money (practice) investment.

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "symbol": "BITCOIN",
  "amount": 100.00
}
```

**Response** (200):
```json
{
  "success": true,
  "investment": {
    "symbol": "BITCOIN",
    "quantity": 0.00220291,
    "purchase_price": 45394.46,
    "amount": 100.00,
    "timestamp": "2026-06-01T20:30:00Z"
  },
  "portfolio": {
    "cash_balance": 99900.00,
    "total_investments": 100.00
  }
}
```

**Errors**:
- `400`: Invalid symbol or amount
- `401`: Unauthorized
- `422`: Validation error

---

### POST `/api/user/portfolio/invest/real`
Make a real money (live) investment via encrypted payment.

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "symbol": "BITCOIN",
  "amount": 100.00,
  "payment_method": "credit_card",
  "encrypted_payment_data": "U2FsdGVkX1..."
}
```

**Response** (200):
```json
{
  "success": true,
  "transaction_id": "TXN_2026-06-01_001",
  "investment": {
    "symbol": "BITCOIN",
    "quantity": 0.00220291,
    "purchase_price": 45394.46,
    "amount": 100.00,
    "timestamp": "2026-06-01T20:30:00Z"
  },
  "portfolio": {
    "cash_balance": 99900.00,
    "total_investments": 100.00
  }
}
```

**Errors**:
- `400`: Invalid symbol, amount, or payment data
- `401`: Unauthorized
- `402`: Payment failed
- `422`: Validation error

---

## Price & Analysis Endpoints

### GET `/api/price/{crypto_id}`
Get current price for a specific cryptocurrency.

**Path Parameters**:
- `crypto_id` (required): Cryptocurrency ID (e.g., `bitcoin`, `ethereum`)

**Response** (200):
```json
{
  "crypto_id": "bitcoin",
  "symbol": "BTC",
  "name": "Bitcoin",
  "price": 71562.34,
  "market_cap": 1408234567890,
  "volume_24h": 45678901234,
  "change_24h": -1250.50,
  "change_24h_percent": -1.72,
  "change_7d_percent": 3.2,
  "change_30d_percent": 8.5,
  "ath": 69045,
  "atl": 67.81,
  "timestamp": "2026-06-01T15:30:00Z"
}
```

---

### GET `/api/prices`
Get current prices for multiple cryptocurrencies.

**Query Parameters**:
- `count` (optional): Number of cryptocurrencies (default: 20, max: 100)
- `sort` (optional): Sort by `market_cap`, `price`, or `volume` (default: `market_cap`)

**Response** (200):
```json
[
  {
    "crypto_id": "bitcoin",
    "symbol": "BTC",
    "price": 71562.34,
    "market_cap": 1408234567890,
    "change_24h_percent": -1.72
  },
  {
    "crypto_id": "ethereum",
    "symbol": "ETH",
    "price": 2002.44,
    "market_cap": 240567890123,
    "change_24h_percent": 0.11
  }
]
```

---

### GET `/api/recommendations`
Get AI-generated investment recommendations.

**Query Parameters**:
- `count` (optional): Number of recommendations (default: 30, max: 50)

**Response** (200):
```json
{
  "recommendations": [
    {
      "symbol": "BITCOIN",
      "name": "Bitcoin",
      "type": "crypto",
      "risk_level": "MEDIUM",
      "category": "LONG_TERM",
      "current_price": 45394.46,
      "allocation_percent": 30.0,
      "reason": "Bitcoin is showing strong uptrend with +0.33% growth in 24h...",
      "market_position": "Price is in an uptrend at $45394.46...",
      "trend": "UPTREND",
      "recommendation": "YES - BUY"
    }
  ],
  "total": 30,
  "generated_at": "2026-06-01T15:30:00Z"
}
```

---

### GET `/api/analysis`
Get comprehensive market analysis.

**Response** (200):
```json
{
  "market_summary": {
    "total_market_cap": 2500000000000,
    "btc_dominance": 48.5,
    "eth_dominance": 18.2,
    "trading_volume_24h": 150000000000,
    "trend": "NEUTRAL"
  },
  "top_movers": {
    "gainers": [{"symbol": "DOGE", "change": 12.5}],
    "losers": [{"symbol": "XRP", "change": -8.3}]
  }
}
```

---

## Alerts Endpoints

### GET `/api/alerts`
Get price alerts based on thresholds.

**Query Parameters**:
- `threshold` (optional): Percentage threshold for alerts (default: 5)

**Response** (200):
```json
{
  "alerts": [
    {
      "symbol": "BITCOIN",
      "current_price": 71562.34,
      "alert_level": 10,
      "message": "Bitcoin is up 10% from alert level"
    }
  ],
  "total": 1
}
```

---

## Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error message explaining what went wrong",
  "status_code": 400,
  "timestamp": "2026-06-01T15:30:00Z"
}
```

**Common Status Codes**:
- `200`: Success
- `201`: Created
- `202`: Accepted (async operation)
- `400`: Bad Request (validation error)
- `401`: Unauthorized (auth required or invalid)
- `402`: Payment Required
- `404`: Not Found
- `429`: Too Many Requests (rate limit)
- `503`: Service Unavailable

---

## WebSocket

### WS `/ws`
Real-time WebSocket connection for price updates.

**Connection**:
```
ws://localhost:8002/ws
```

**Message Format** (received):
```json
{
  "type": "price_update",
  "symbol": "BITCOIN",
  "price": 71562.34,
  "timestamp": "2026-06-01T15:30:00Z"
}
```

---

## Rate Limits

| Source | Limit | Notes |
|--------|-------|-------|
| CoinGecko | 50/min | 5-min cache applied |
| Yahoo Finance | Unlimited | No official limit |
| Alpha Vantage | 5/min, 500/day | Demo key very limited |
| CoinMarketCap | 333/day | Free tier |
| Binance | 1200/min | Direct API limit |

---

## Authentication Details

**JWT Token Structure**:
- Algorithm: HS256
- Expiration: 24 hours from issue
- Header: `Authorization: Bearer <token>`

**Password Hashing**:
- Algorithm: PBKDF2-SHA256 (pure Python, Windows-compatible)
- No external C dependencies required

**Encryption**:
- Client-side: AES-GCM-256 (Web Crypto API)
- Server-side: cryptography 48.0.0 library

---

## Environment Variables

Create `.env` file with:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=crypto_ai
SECRET_KEY=your-secret-key-here

# Optional API Keys
ALPHA_VANTAGE_API_KEY=demo
COINMARKETCAP_API_KEY=your-key-here

# Trading
ALPACA_API_KEY=your-key
ALPACA_SECRET_KEY=your-secret
BINANCE_API_KEY=your-key
BINANCE_API_SECRET=your-secret

# ML/AI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## Testing

### Postman Collection
Use endpoint examples above to test in Postman:
1. Register user
2. Login to get token
3. Use token for authenticated requests
4. Test investment flows with fake money first

### cURL Examples

**Login**:
```bash
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'
```

**Get Prices**:
```bash
curl http://localhost:8002/api/prices?count=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Make Investment**:
```bash
curl -X POST http://localhost:8002/api/user/portfolio/invest/fake \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BITCOIN","amount":100}'
```

---

## Support

For issues or questions:
1. Check MongoDB logs: `logs/mongodb.log`
2. Check backend logs: Terminal output
3. Check browser console: DevTools F12
4. Review error responses in network tab
