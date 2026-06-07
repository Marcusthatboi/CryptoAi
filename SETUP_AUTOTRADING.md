# Auto Trading Setup Guide

## Status Summary
✅ **Implemented:**
- Binance API integration (backend)
- Auto trading routes (preview, execute, active-trades)
- Frontend UI (3 tabs: Warnings, Execute, Active Trades)
- MongoDB persistence for trades
- CORS configuration for localhost development
- Premium subscription gating

❌ **Still Need:**
1. Binance API keys configured in .env
2. Frontend authentication flow fixed
3. Windows Service for auto-start

---

## Step 1: Get Binance API Keys

### For TESTNET (Recommended First):
1. Go to: https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key"
3. Use **Testnet** API key and secret
4. Create `.env` file in project root:
   ```
   BINANCE_API_KEY=your_testnet_api_key
   BINANCE_API_SECRET=your_testnet_api_secret
   BINANCE_TESTNET=true
   BINANCE_TLD=com
   ```

### For MAINNET (Real Money):
1. Go to: https://www.binance.com/en/user/settings/api-management
2. Click "Create API"
3. Choose "Server" type
4. Enable "Spot Trading Permission"
5. Update `.env`:
   ```
   BINANCE_API_KEY=your_mainnet_api_key
   BINANCE_API_SECRET=your_mainnet_api_secret
   BINANCE_TESTNET=false
   BINANCE_TLD=us  # Use 'us' for Binance.US
   ```

---

## Step 2: Verify Connection

1. Start backend:
   ```bash
   cd C:\Users\marcu\CryproAI
   cmd /c start_backend.bat
   ```

2. Test Binance connection (in PowerShell):
   ```powershell
   $token = "your_test_token"  # Get from login
   Invoke-WebRequest -Uri "http://localhost:8002/api/binance/status" `
     -Headers @{"Authorization" = "Bearer $token"} `
     -UseBasicParsing | ConvertFrom-Json
   ```

3. Expected response:
   ```json
   {
     "connected": true,
     "testnet": true/false,
     "account_balance": 1000.50,
     "currencies": ["BTC", "ETH", ...]
   }
   ```

---

## Step 3: Test Auto Trading Flow

1. **Login** (testuser_autotrading / TestPassword123!)
2. **Navigate** to http://localhost:5174/auto-trading
3. **View Warnings** tab (should show 15 trading warnings)
4. **Execute Trade** tab:
   - Symbol: BTCUSDT
   - Action: BUY
   - Quantity: 0.001
   - Stop Loss: 59000
   - Take Profit: 65000
   - Check both acknowledgment boxes
   - Click "Preview Trade"
5. **Review** risk calculations
6. **Confirm** and execute trade
7. **Monitor** in "Active Trades" tab

---

## Step 4: Setup Windows Service (For Production)

See `SETUP_WINDOWS_SERVICE.bat` for automatic setup.

Or manually:
1. Run as Administrator
2. Execute: `nssm install CryptoAI-Backend C:\Users\marcu\CryproAI\start_backend.bat`
3. Execute: `nssm install CryptoAI-Frontend C:\Users\marcu\CryproAI\start_frontend.bat`
4. Services will auto-start on reboot

---

## Troubleshooting

### "Binance credentials not configured"
- Check `.env` file exists in project root
- Verify BINANCE_API_KEY and BINANCE_API_SECRET are set
- Backend requires restart after .env changes

### "401 Unauthorized" on /auto-trading
- Login redirects to login loop = auth validation issue
- Clear browser localStorage (F12 → Application → Local Storage → Clear)
- Try again

### "CORS error" 
- This is fixed with start_backend.bat
- Ensure backend is started with `cmd /c start_backend.bat`
- Don't use direct uvicorn command

---

## Production Deployment Checklist

- [ ] .env configured with MAINNET Binance keys (BINANCE_TESTNET=false)
- [ ] Windows Service installed and running
- [ ] Backend health check: http://localhost:8002/health → 200 OK
- [ ] Frontend loads: http://localhost:5174 (or production domain)
- [ ] Test account created with Premium tier
- [ ] Small test trade executed successfully
- [ ] Active Trades tab shows trade
- [ ] MongoDB auto_trades collection contains trades
- [ ] Cloudflare tunnel active (for HTTPS)
- [ ] Stripe payment integration enabled
