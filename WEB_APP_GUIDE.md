# CryptoAI Web Application - Setup & Usage

## 🚀 Quick Start

### Option 1: Start Everything (Recommended)

**Windows:**
```powershell
cd c:\Users\marcu\CryproAI
.\start.bat
```

**macOS/Linux:**
```bash
cd ~/CryproAI
bash start.sh
```

This will automatically:
- Create/activate virtual environment
- Install all dependencies
- Start the FastAPI backend (port 8000)
- Start the React frontend (port 3000)

### Option 2: Start Services Separately

**Backend Only:**

Windows:
```powershell
.\start_backend.bat
```

macOS/Linux:
```bash
bash start_backend.sh
```

Backend runs at: **http://localhost:8000**

**Frontend Only:**

Windows:
```powershell
.\start_frontend.bat
```

macOS/Linux:
```bash
bash start_frontend.sh
```

Frontend runs at: **http://localhost:3000**

---

## 📋 Prerequisites

### Windows
```powershell
# Install Node.js (if not installed)
# Download from: https://nodejs.org/

# Check versions
node --version
npm --version
python --version
```

### macOS
```bash
# Using Homebrew
brew install node
brew install python@3.11
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install nodejs npm python3 python3-venv
```

---

## 🏗️ Project Structure

```
CryproAI/
├── backend/
│   └── main.py              # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── PriceCard.jsx
│   │   │   ├── TrendChart.jsx
│   │   │   └── AlertPanel.jsx
│   │   ├── utils/
│   │   │   └── api.js       # API client
│   │   ├── App.jsx          # Main app
│   │   └── main.jsx         # React entry
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── src/
│   └── crypto_tracker.py    # Shared backend logic
├── requirements.txt
├── start.bat / start.sh
├── start_backend.bat / start_backend.sh
└── start_frontend.bat / start_frontend.sh
```

---

## 🔌 API Endpoints

### Health Check
```
GET /health
```

### Price Data
```
GET /api/price/{crypto_id}          # Single price
POST /api/prices                      # Multiple prices
GET /api/prices/refresh              # Update prices
```

### Analysis
```
GET /api/analysis/{crypto_id}        # Single trend
GET /api/analysis                    # All trends
```

### Alerts
```
GET /api/alerts                      # Get active alerts
```

### History
```
GET /api/history/{crypto_id}         # Historical data
```

### ML Data
```
GET /api/ml-data/{crypto_id}         # ML preparation
```

### Statistics
```
GET /api/stats                       # Dataset statistics
GET /api/config                      # API configuration
```

### API Documentation
```
http://localhost:8000/docs           # Interactive Swagger UI
http://localhost:8000/redoc          # ReDoc documentation
```

---

## 🎯 Frontend Features

### Dashboard Components

**Price Cards**
- Live cryptocurrency prices
- 24h price change percentage
- Market cap & volume
- 30-second auto-refresh
- Click to select for chart

**Trend Chart**
- Interactive price history chart
- Hover tooltips
- Animated line chart
- 50 data points displayed

**Alert Panel**
- Active price alerts
- Real-time notification system
- Alert direction (UP/DOWN)
- 60-second refresh
- Empty state for no alerts

**Statistics**
- Total records in database
- Number of tracked cryptocurrencies
- Last update timestamp
- Real-time sync

---

## 🔧 Configuration

### Backend (backend/main.py)

Edit the defaults in the FastAPI setup:
```python
DEFAULT_CRYPTOCURRENCIES = ["bitcoin", "ethereum"]  # Line ~80
PRICE_CHANGE_THRESHOLD = 5.0                       # Alert threshold
SMA_WINDOW = 5                                       # Moving average window
```

### Frontend (frontend/src/utils/api.js)

Change API base URL if needed:
```javascript
const API_BASE = 'http://localhost:8000'  // Line ~3
```

---

## 💻 Development

### Backend Development

Install dev dependencies:
```powershell
pip install -r requirements.txt
```

Run with auto-reload:
```powershell
python backend/main.py
```

Hot-reload is enabled by default (Uvicorn with reload=True).

### Frontend Development

Install dev dependencies:
```powershell
cd frontend
npm install
```

Run dev server with hot reload:
```powershell
npm run dev
```

Build for production:
```powershell
npm run build
```

Preview production build:
```powershell
npm run preview
```

---

## 🌐 Accessing the Application

### Once services are running:

1. **Frontend Dashboard**
   - Open: **http://localhost:3000**
   - View live prices, charts, and alerts

2. **API Documentation**
   - Swagger: **http://localhost:8000/docs**
   - ReDoc: **http://localhost:8000/redoc**

3. **Direct API Calls**
   ```bash
   # Example: Get Bitcoin price
   curl http://localhost:8000/api/price/bitcoin
   ```

---

## 🐛 Troubleshooting

### Port Already in Use

If port 3000 or 8000 is already in use:

**Find and kill process:**

Windows:
```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F

netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

macOS/Linux:
```bash
lsof -i :3000
kill -9 <PID>

lsof -i :8000
kill -9 <PID>
```

**Change ports in Vite config:**

Edit `frontend/vite.config.js`:
```javascript
server: {
  port: 3001,  // Changed from 3000
  proxy: { ... }
}
```

### Dependencies Not Installing

```powershell
# Clear npm/pip cache
npm cache clean --force
pip cache purge

# Reinstall dependencies
cd frontend
npm install --no-cache

cd ..
pip install -r requirements.txt --no-cache-dir
```

### Frontend Can't Connect to Backend

Check that backend is running:
```powershell
# Test API
curl http://localhost:8000/health
```

If backend not responding:
1. Check port 8000 is not blocked
2. Verify backend process is running
3. Check browser console for CORS errors

### No Data in Dashboard

The CSV file needs data points. Generate data:
```powershell
python src/crypto_tracker.py
```

Then refresh the dashboard (Ctrl+F5 for hard refresh).

---

## 📦 Building for Production

### Backend

Use Gunicorn for production:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
```

### Frontend

Build optimized bundle:
```bash
cd frontend
npm run build
# Output in: frontend/dist/
```

Deploy `frontend/dist/` to any static host (Netlify, Vercel, etc.)

---

## 🔒 Security Notes

### Current Setup (Development Only)

- CORS allows localhost only
- No authentication required
- Local file storage only

### For Production:

1. Enable authentication (JWT tokens)
2. Restrict CORS to specific domains
3. Move CSV to database (MongoDB)
4. Use environment variables for configuration
5. Add rate limiting to API
6. Enable HTTPS/SSL
7. Add input validation
8. Implement vote limit on API requests

---

## 📊 Example Workflow

1. **Start application**
   ```
   .\start.bat  (or bash start.sh)
   ```

2. **Wait for startup** (~30 seconds)
   - Backend starts on port 8000
   - Frontend starts on port 3000
   - Two windows will open automatically

3. **Open dashboard**
   - Browser opens to http://localhost:3000
   - See live prices and charts

4. **Generate data** (if needed)
   ```powershell
   python src/crypto_tracker.py
   ```

5. **Refresh dashboard**
   - Press Ctrl+F5 to hard refresh
   - New data appears in charts

6. **Stop services**
   - Ctrl+C in both windows
   - Or close terminal windows

---

## 🚀 Next Steps

- Customize tracked cryptocurrencies
- Add more technical indicators
- Integrate database (MongoDB)
- Deploy to cloud (Heroku, AWS, Vercel)
- Add user authentication
- Create trading alerts
- Build mobile app

---

## 📞 API Reference

See interactive docs at: **http://localhost:8000/docs**

Full API reference available after backend starts.

---

**Ready to track crypto? Run `.\start.bat` or `bash start.sh` now!** 🚀💰
