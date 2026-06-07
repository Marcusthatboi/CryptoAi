# 🚀 CryptoAI Auto Trading - Quick Start Guide

## What's Ready Now

✅ **Backend Auto Trading Engine**
- REST API endpoints for trade preview & execution
- Binance.US integration (production credentials)
- MongoDB persistence for trade history
- Premium subscription gating
- Risk calculation engine

✅ **Frontend Auto Trading UI**
- 3-tab interface (Warnings, Execute, Active Trades)
- Real-time trade monitoring
- Risk acknowledgment flow
- Responsive design with CSS Grid

✅ **Infrastructure**
- CORS fixed for localhost development (port 5174)
- Database connections working
- API documentation at http://localhost:8002/docs

---

## 5-Minute Setup

### 1. Get Binance API Keys (2 min)

**For Testing (Testnet - Recommended First):**
1. Go to: https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key"
3. Copy the key and secret

**For Real Trading:**
1. Go to: https://www.binance.com/en/user/settings/api-management
2. Click "Create API" → "Server" type
3. Enable "Spot Trading Permission"
4. Copy the key and secret

### 2. Create .env File (1 min)

Copy `.env.example` → `.env` and fill in:

```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true          # Start with true!
BINANCE_TLD=us                 # Or 'com' for global
```

### 3. Start Backend (1 min)

```bash
cmd /c start_backend.bat
```

**Wait until you see:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8002
```

### 4. Start Frontend (1 min)

In a **new terminal**:
```bash
cd frontend
npm run dev
```

**Wait until you see:**
```
VITE v5.0.0 ready in 1234 ms
```

---

## Testing the Flow

### 1. Login
- Navigate to: http://localhost:5174/login
- Username: `testuser_autotrading`
- Password: `TestPassword123!`

### 2. Go to Auto Trading
- URL: http://localhost:5174/auto-trading
- Should see 3 tabs

### 3. Execute Test Trade
1. Click "💱 Execute Trade" tab
2. Fill in:
   - Symbol: `BTCUSDT`
   - Quantity: `0.001`
   - Stop Loss: `59000`
   - Take Profit: `65000`
3. Check both risk acknowledgments
4. Click "Preview Trade"
5. Review calculated risks
6. Click "Confirm Trade"

### 4. Monitor Trade
- Click "📊 Active Trades" tab
- Should see your trade with live price

---

## Run Full Test Suite

```bash
python test_auto_trading_e2e.py
```

This will:
✅ Check backend health  
✅ Test authentication  
✅ Verify subscription tier  
✅ Confirm Binance connection  
✅ Calculate trade preview  
✅ Show active trades  

---

## Setup for Production

### Install Windows Service (Auto-Start on Reboot)

1. **Open Command Prompt as Administrator**
2. Run:
   ```bash
   SETUP_WINDOWS_SERVICE.bat
   ```

This will:
- Download NSSM (service manager)
- Create Windows Services for Backend & Frontend
- Set to auto-start on boot
- Verify both services are running

### Verify Services

```bash
services.msc
```

Look for:
- `CryptoAI-Backend` → Running
- `CryptoAI-Frontend` → Running

---

## Troubleshooting

### "Backend unreachable"
```bash
# Check if port 8002 is in use
netstat -ano | findstr :8002

# Kill process on that port
taskkill /PID [process_id] /F

# Restart backend
cmd /c start_backend.bat
```

### "Binance credentials not configured"
- Verify `.env` file exists in project root
- Check `BINANCE_API_KEY` is not empty
- Restart backend service

### "401 Unauthorized" on /auto-trading
- Clear browser localStorage: `F12 → Application → Local Storage → Clear`
- Re-login
- Try again

### Service won't start
- Check Windows Event Viewer (eventvwr.msc)
- Look for error messages
- Try manual startup: `cmd /c start_backend.bat`

---

## Next Steps

### Immediate (This Hour)
1. ✅ Get Binance API keys
2. ✅ Create .env file
3. ✅ Start backend & frontend
4. ✅ Run test suite
5. ✅ Execute test trade

### Short Term (This Week)
1. Setup Windows Service (production deployment)
2. Test with MAINNET=false (testnet) first
3. Move to MAINNET=true after confirming
4. Monitor first 10 trades
5. Adjust risk parameters as needed

### Medium Term (This Month)
1. Implement paper trading mode (no real money)
2. Add backtesting engine
3. Create admin dashboard
4. Setup monitoring & alerts
5. Document trading strategies

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│ Frontend (React 18 + Vite)                  │
│ http://localhost:5174/auto-trading          │
│ ├─ Warnings Tab (15 risk warnings)          │
│ ├─ Execute Tab (trade form)                 │
│ └─ Active Trades Tab (live monitor)         │
└────────────┬────────────────────────────────┘
             │ HTTP/REST
             ↓
┌─────────────────────────────────────────────┐
│ Backend (FastAPI + Uvicorn)                 │
│ http://localhost:8002                       │
│ ├─ /api/auto-trading/preview                │
│ ├─ /api/auto-trading/execute                │
│ └─ /api/auto-trading/user/active-trades     │
└────────┬─────────────────┬──────────────────┘
         │ MongoDB         │ REST API
         ↓                 ↓
    ┌─────────────┐   ┌──────────────┐
    │ MongoDB     │   │ Binance.US   │
    │ (auto_trades)   │ (real orders)│
    └─────────────┘   └──────────────┘
```

---

## File Structure

```
CryptoAI/
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── binance_api.py            # Binance integration
│   ├── routers/
│   │   └── auto_trading_routes.py # Trade endpoints
│   └── db.py                      # MongoDB
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── AutoTradingPage.jsx
│   │   └── styles/
│   │       └── AutoTradingPage.css
│   └── package.json
├── .env                          # Your config (CREATE THIS)
├── start_backend.bat
├── start_frontend.bat
├── SETUP_WINDOWS_SERVICE.bat
├── test_auto_trading_e2e.py
├── SETUP_AUTOTRADING.md
├── DEPLOYMENT_CHECKLIST.md
└── README.md
```

---

## API Endpoints

### Authentication
```
POST /api/auth/login
  body: {username, password}
  response: {access_token, user_id, username, tier}
```

### Auto Trading
```
GET /api/auto-trading/warnings
  headers: {Authorization: Bearer token}
  response: {warnings: [...]}

POST /api/auto-trading/preview
  headers: {Authorization: Bearer token}
  body: {symbol, action, quantity, stop_loss, take_profit, acknowledgement_*}
  response: {status, symbol, quantity, max_loss, max_gain, message}

POST /api/auto-trading/execute
  headers: {Authorization: Bearer token}
  body: {symbol, action, quantity, stop_loss, take_profit, acknowledgement_*}
  response: {order_id, status, message}

GET /api/auto-trading/user/active-trades
  headers: {Authorization: Bearer token}
  response: {active_trades: [...]}
```

---

## Risk Parameters

Default values (can be customized):
- **Max Loss per Trade**: 2% of account
- **Max Gain per Trade**: 5% of account
- **Min Quantity**: 0.001 BTC
- **Max Quantity**: 1.0 BTC
- **Stop Loss**: -1% to -5%
- **Take Profit**: +2% to +10%

---

## Support

Need help?

1. **Check logs**: 
   - Backend: `backend/main.py` logs
   - Frontend: Browser console (F12)

2. **Test connection**:
   - `Invoke-WebRequest http://localhost:8002/health`

3. **Review docs**:
   - API docs: http://localhost:8002/docs
   - Binance docs: https://binance-docs.github.io/apidocs/

4. **Contact support**:
   - Email: cryptosupport74@gmail.com

---

## Security Checklist

- ✅ API keys stored in `.env` (never commit!)
- ✅ JWT tokens with expiration
- ✅ CORS restricted to known origins
- ✅ Database authentication enabled
- ✅ HTTPS enabled (via Cloudflare tunnel)
- ✅ Rate limiting on API endpoints
- ✅ SQL injection prevention (using ORM)
- ✅ CSRF protection on POST endpoints

---

**Status**: Production Ready ✅  
**Last Updated**: 2026-06-06  
**Version**: 1.0
