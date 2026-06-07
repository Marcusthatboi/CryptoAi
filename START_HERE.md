# 🚀 CryptoAI Web Application - Start Here

## ✅ Everything is Ready!

Your full-stack web application is complete. Here's how to start it:

---

## 🎯 QUICK START (One Command)

### Windows - PowerShell
```powershell
cd c:\Users\marcu\CryproAI
.\start.bat
```

### macOS/Linux - Bash
```bash
cd ~/CryproAI
bash start.sh
```

**That's it!** The script will:
1. ✓ Create/activate virtual environment
2. ✓ Install all Python & Node dependencies
3. ✓ Start FastAPI backend (port 8000)
4. ✓ Start React frontend (port 3000)
5. ✓ Open your browser to the dashboard

---

## 📖 What Gets Started

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Interactive cryptocurrency dashboard |
| **Backend API** | http://localhost:8000 | REST API server |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |

---

## 🛠️ Manual Startup (If Needed)

### Terminal 1: Start Backend
```powershell
cd c:\Users\marcu\CryproAI
.\.venv\Scripts\Activate.ps1
python backend/main.py
```

**Output should show:**
```
INFO:     Application startup complete
Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Start Frontend
```powershell
cd c:\Users\marcu\CryproAI\frontend
npm run dev
```

**Output should show:**
```
Local:   http://localhost:3000
```

---

## 🎨 Frontend Dashboard

### What You'll See:

1. **Header** - CryptoAI branding and description
2. **Statistics** - Total records, cryptocurrencies tracked, last update time
3. **Price Cards** - Live Bitcoin & Ethereum prices with 24h change
4. **Alert Panel** - Active price alerts (5% threshold)
5. **Price Charts** - Interactive trend visualization
6. **Auto-refresh** - Updates every 30 seconds

### How to Use:

- **View prices** - Scroll to see current prices
- **Select crypto** - Click on any price card to view its chart
- **View trends** - Chart updates below showing price history
- **Check alerts** - View active price alerts in alert panel
- **Refresh data** - Button to manually refresh alerts

---

## 🔌 API Endpoints

### Get Live Prices
```
GET http://localhost:8000/api/price/bitcoin
GET http://localhost:8000/api/price/ethereum
```

### Get Multiple Prices
```
POST http://localhost:8000/api/prices
Body: ["bitcoin", "ethereum", "cardano"]
```

### Get Trend Analysis
```
GET http://localhost:8000/api/analysis/bitcoin
GET http://localhost:8000/api/analysis (all cryptos)
```

### Get Alerts
```
GET http://localhost:8000/api/alerts
```

### Get Historical Data
```
GET http://localhost:8000/api/history/bitcoin?limit=50
```

### Interactive API Docs
```
http://localhost:8000/docs
```

Try out all endpoints directly in the Swagger UI!

---

## 📊 Generate More Data

The dashboard works best with historical data. Generate more data points:

```powershell
python src/crypto_tracker.py
```

Run multiple times (wait 30 seconds between runs) to see trends in the chart.

**After generating data:**
1. Hard refresh browser (Ctrl+F5)
2. Charts will show price history
3. More trends become visible

---

## 🔍 Troubleshooting

### "Port 3000 is already in use"
```powershell
# Find and kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### "Cannot find module 'react'"
```powershell
cd frontend
npm install
```

### "No data in dashboard"
```powershell
# Generate price data
python src/crypto_tracker.py

# Then refresh browser (Ctrl+F5)
```

### "Backend not responding"
```powershell
# Verify backend is running
Invoke-WebRequest http://localhost:8000/health
```

---

## 📝 Project Structure

```
CryproAI/
├── backend/
│   └── main.py                 # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── App.jsx            # Main dashboard
│   │   └── main.jsx           # React entry point
│   ├── package.json
│   └── index.html
├── src/
│   └── crypto_tracker.py       # Shared logic
├── data/
│   └── crypto_prices.csv       # Historical data
├── plots/
│   └── *.png                  # Generated charts
└── start.bat / start.sh        # Quick start scripts
```

---

## 🎓 Example Workflows

### Workflow 1: View Live Prices
1. Run `.\start.bat`
2. Open http://localhost:3000
3. See current Bitcoin & Ethereum prices
4. Prices auto-refresh every 30 seconds

### Workflow 2: Generate & View Trends
1. Run `python src/crypto_tracker.py`  (generates data)
2. Open http://localhost:3000
3. Hard refresh (Ctrl+F5)
4. Click on any price card
5. See price history chart below

### Workflow 3: Test API Directly
1. Run `.\start.bat`
2. Open http://localhost:8000/docs
3. Try out any endpoint interactively
4. See live API responses

### Workflow 4: Monitor Alerts
1. Run `.\start.bat`
2. Check Alert Panel on dashboard
3. Button to manually refresh alerts
4. Shows price changes > 5%

---

## 🚀 Next Steps

1. **Customize Cryptocurrencies**
   - Edit `backend/main.py`
   - Change line ~400 in `DEFAULT_CRYPTOCURRENCIES`

2. **Generate More Data**
   - Run `python src/crypto_tracker.py` multiple times
   - Better trends appear with more history

3. **Deploy to Cloud**
   - Backend: Heroku, Railway, Render
   - Frontend: Vercel, Netlify, GitHub Pages

4. **Add Features**
   - More technical indicators
   - User accounts
   - Push notifications
   - Trading signals

---

## 📞 API Documentation

**Full interactive docs** available at:
```
http://localhost:8000/docs
```

Try any endpoint with live examples!

---

## ✨ Features Included

- ✅ Real-time cryptocurrency prices
- ✅ Historical data tracking
- ✅ Price trend analysis with SMA
- ✅ Automatic price alerts
- ✅ Interactive charts
- ✅ Multi-cryptocurrency support
- ✅ REST API with full documentation
- ✅ React dashboard UI
- ✅ Auto-refreshing data
- ✅ Production-ready code

---

## 💡 Pro Tips

1. **API is RESTful** - Use any HTTP client (curl, Postman, etc.)
2. **Real CORS enabled** - Frontend can call backend from different port
3. **Hourly updates** - Run `crypto_tracker.py` with task scheduler for live data
4. **Database ready** - Can migrate CSV to MongoDB/PostgreSQL later
5. **ML prepared** - `/api/ml-data` endpoint provides prepared features

---

## ⏱️ First Run Timeline

1. **Command:** `.\start.bat` (0s)
2. **Virtual env setup** (3s)
3. **Dependencies install** (30s)
4. **Backend starts** (5s) ➜ Ready at http://localhost:8000
5. **Frontend starts** (15s) ➜ Ready at http://localhost:3000
6. **Display market data** (5s) ➜ Dashboard loads

**Total: ~60 seconds** ✨

---

## 🎉 You're All Set!

Your production-grade cryptocurrency dashboard is ready!

### To get started:

```powershell
cd c:\Users\marcu\CryproAI
.\start.bat
```

The dashboard will open automatically. Enjoy! 🚀💰

---

**Questions?** Check [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) for detailed documentation.
