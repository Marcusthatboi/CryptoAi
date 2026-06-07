# API Documentation

Base URL (local): `http://localhost:8002`

Authentication model:
- Protected routes require `Authorization: Bearer <jwt>`
- JWT tokens are issued by `/auth/register` and `/auth/login`

Transport model:
- REST API over HTTP
- WebSocket endpoint at `/ws` for realtime price updates

## 1) Authentication

### POST /auth/register
Register a user account and return token payload.

Request body:
```json
{
  "username": "trader",
  "password": "StrongPass123",
  "email": "trader@example.com"
}
```

Response fields:
- `access_token`
- `token_type`
- `username`
- `user_id`
- `is_admin`
- `role`
- `expires_in`

### POST /auth/login
Authenticate and return token payload.

### GET /auth/profile
Protected. Returns profile metadata including role/admin flags.

## 2) Core Market Data

### GET /health
Health probe endpoint.

### GET /api/price/{crypto_id}
Fetch current quote for one asset.

### POST /api/prices
Fetch current quotes for multiple assets.

Request body:
```json
["bitcoin", "ethereum", "solana"]
```

### GET /api/prices/refresh
Trigger data refresh pipeline.

### GET /api/history/{crypto_id}
Fetch historical records.

### GET /api/stats
General market and record stats for dashboard cards.

### GET /api/config
Server-side runtime config summary.

## 3) Analysis, Alerts, AI

### GET /api/analysis/{crypto_id}
Trend analysis for a single asset.

### GET /api/analysis
Trend analysis for tracked universe.

### GET /api/alerts
Price-change based alert list.

### GET /api/ml-data/{crypto_id}
ML feature preparation payload.

### POST /api/chat
AI chat endpoint for crypto assistant interactions.

Notes:
- Endpoint has per-actor rate limiting.
- Returns HTTP 429 with `Retry-After` when exceeded.

### GET /api/recommendations
AI recommendations endpoint.

Notes:
- Enforces subscription quotas.
- May return 403 for daily signal limit exhaustion.
- May return 429 for hourly API quota exhaustion.

## 4) User Portfolio

### GET /api/user/portfolio
Protected. Returns user portfolio state.

### POST /api/user/portfolio/invest
Protected. Generic investment operation.

### POST /api/user/portfolio/invest/fake
Protected. Execute investment using virtual cash.

### POST /api/user/portfolio/invest/real
Protected. Execute investment using real-money lane.

### GET /api/user/holdings
Protected. Returns holdings list.

## 5) Subscription and Billing

### GET /api/subscription/pricing/plans
Public. Returns plan metadata and limits.

### GET /api/subscription/benefits/{tier}
Public. Returns benefit details for tier.

### GET /api/subscription/status
Protected. Returns user subscription status.

### GET /api/subscription/usage-summary
Protected. Returns quota/usage counters and reset timestamps.

### POST /api/subscription/create-payment-intent
Protected. Creates Stripe payment intent for upgrade flow.

### POST /api/subscription/create-checkout-session
Protected. Creates hosted checkout session (used for wallet/QR flow).

### POST /api/subscription/upgrade
Protected. Applies subscription upgrade after successful payment.

### POST /api/subscription/cancel
Protected. Cancels and downgrades plan state.

### POST /api/subscription/webhook
Stripe webhook receiver for billing lifecycle sync.

## 6) Admin APIs

### GET /api/subscription/analytics/overview
Protected (admin-only). Monetization and quota pressure overview.

### GET /api/admin/customers
Protected (admin-only). Customer management dataset.

Supported query params:
- `search`
- `tier`
- `status_filter`
- `limit`

### PATCH /api/admin/customers/{user_id}/subscription
Protected (admin-only). Support operation to adjust tier/status.

Request body:
```json
{
  "tier": "pro",
  "status": "active"
}
```

## 7) Provider Integrations

### Ollama
- GET `/api/ollama/status`
- POST `/api/ollama/switch-model/{model_name}`

### Alpaca
- GET `/alpaca/account`
- GET `/alpaca/holdings`
- GET `/alpaca/quote/{symbol}`
- POST `/alpaca/order`
- DELETE `/alpaca/order/{order_id}`
- GET `/alpaca/orders`
- GET `/alpaca/account/user`

### Binance
- GET `/api/binance/status`
- GET `/api/binance/account`
- GET `/api/binance/balance`
- GET `/api/binance/portfolio`
- GET `/api/binance/ticker/{symbol}`
- GET `/api/binance/klines/{symbol}`
- GET `/api/binance/gainers`
- POST `/api/binance/trade`
- POST `/api/binance/cancel-order`
- GET `/api/binance/order-status`
- GET `/api/binance/open-orders`
- GET `/api/binance/order-history`
- GET `/api/binance/trading-pairs`
- GET `/api/binance/search/{query}`

### Multi-source Market Data
- GET `/api/data-sources/status`
- GET `/api/data/coingecko`
- GET `/api/data/yahoo-finance`
- GET `/api/data/alpha-vantage/stock/{symbol}`
- GET `/api/data/alpha-vantage/forex/{from_symbol}/{to_symbol}`
- GET `/api/data/coinmarketcap`
- POST `/api/data/collect`
- GET `/api/data/export`

## 8) WebSocket API

Endpoint: `ws://localhost:8002/ws`

Typical client messages:
```json
{ "type": "subscribe", "symbol": "BITCOIN" }
```
```json
{ "type": "unsubscribe", "symbol": "BITCOIN" }
```

Typical server event:
```json
{
  "type": "price_update",
  "symbol": "BITCOIN",
  "data": {
    "price": 68000.12,
    "timestamp": "2026-06-02T18:52:00"
  }
}
```

## 9) Error Model

Common HTTP statuses:
- 400: invalid input
- 401: authentication missing/invalid
- 403: permission denied or quota policy block
- 404: entity not found
- 429: request rate limit or hourly API quota exceeded
- 500: server error
- 503: subsystem unavailable

Rate-limited responses include:
- `Retry-After` header when available

## 10) API Maintenance Notes

- Use `backend/main.py` as the canonical route map.
- Keep docs in sync when adding/changing routes, params, or response fields.
- For breaking changes, version either by path prefix or explicit changelog section in this file.
