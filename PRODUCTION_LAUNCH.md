# 🚀 CryptoAI Production Launch Guide

## Quick Start (5 seconds)

Double-click: **`start_production.bat`**

All services will launch in minimized windows:
- ✅ Backend API on http://127.0.0.1:8002
- ✅ Cloudflare Tunnel routing all domains
- ✅ Frontend dev server on http://localhost:5173

## Service Status

### Backend API
- **URL**: https://api.dacryptobeast.com
- **Local**: http://127.0.0.1:8002
- **Docs**: https://api.dacryptobeast.com/docs
- **Health**: https://api.dacryptobeast.com/health
- **Framework**: FastAPI + Uvicorn
- **Database**: MongoDB (cryptoai)

### Cloudflare Tunnel
- **Tunnel Name**: dacryptobeast-root
- **Status**: 4 connections to Cloudflare edge
- **Routes**:
  - dacryptobeast.com → 127.0.0.1:8002
  - www.dacryptobeast.com → 127.0.0.1:8002
  - api.dacryptobeast.com → 127.0.0.1:8002

### Frontend
- **Dev Server**: http://localhost:5173
- **Production Build**: `/frontend/dist/`
- **Framework**: React + Vite
- **Branding**: DaCryptoBeast

## Available Endpoints (from spec)

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/profile` - Get user profile
- `POST /auth/forgot-password` - Forgot password
- `POST /auth/reset-password` - Reset password with token

### Portfolio
- `GET /api/user/portfolio` - Portfolio summary
- `POST /api/user/portfolio/invest/fake` - Fake investment
- `POST /api/user/portfolio/invest/real` - Real investment

### Real-time (WebSocket)
- Endpoint: `/ws` or `/ws/{client_id}`
- Transport: `wss://api.dacryptobeast.com/ws`
- Topics:
  - `price_update` - Live price changes
  - `portfolio_update` - Portfolio changes
  - `alert_update` - User alerts

### System
- `GET /health` - Health check
- `GET /docs` - API documentation

## Testing

### Backend Health
```powershell
Invoke-RestMethod 'https://api.dacryptobeast.com/health' | ConvertTo-Json
```

### Frontend Access
```
http://localhost:5173
```

### API Docs
```
https://api.dacryptobeast.com/docs
```

## Persistence Options

### Option 1: Manual Startup
Run `start_production.bat` after each reboot.

### Option 2: Windows Task Scheduler (Auto-start on boot)
1. Open Task Scheduler
2. Create Basic Task
3. Name: "CryptoAI Production"
4. Trigger: "At startup"
5. Action: "Start program" → `C:\Users\marcu\CryproAI\start_production.bat`

### Option 3: Startup Folder
Copy `start_production.bat` to:
```
C:\Users\marcu\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

## Stopping Services

To stop all services, double-click: **`stop_production.bat`**

Or manually:
```powershell
taskkill /FI "WINDOWTITLE eq CryptoAI*" /T /F
```

## Logs

Check service windows for real-time logs. All three services run in separate minimized windows you can maximize anytime.

## Troubleshooting

### "Module not found" errors
```powershell
cd C:\Users\marcu\CryproAI
python -m pip install -r requirements.txt
```

### Frontend npm issues
```powershell
cd C:\Users\marcu\CryproAI\frontend
npm install
npm run dev
```

### Tunnel not connecting
```powershell
cloudflared tunnel login
cloudflared tunnel run dacryptobeast-root
```

### Port already in use
```powershell
# Find what's using port 8002
netstat -ano | findstr :8002
# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

## Public URLs

| Service | URL |
|---------|-----|
| Main Domain | https://dacryptobeast.com |
| WWW Domain | https://www.dacryptobeast.com |
| API Domain | https://api.dacryptobeast.com |
| API Docs | https://api.dacryptobeast.com/docs |
| Health Check | https://api.dacryptobeast.com/health |
| Frontend (dev) | http://localhost:5173 |

## Environment Variables

Frontend (.env.local):
```
VITE_API_BASE_URL=https://api.dacryptobeast.com
VITE_WS_URL=wss://api.dacryptobeast.com
```

Backend (.env):
```
DATABASE_URL=mongodb://localhost:27017
ADMIN_USERNAME=admin
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
```

## Next Steps

1. ✅ Backend running
2. ✅ Tunnel running
3. ✅ Frontend built
4. ⏳ Setup auto-start on reboot (optional, see Persistence Options above)
5. ⏳ Deploy frontend to production server (optional)

## Support

For issues or questions about:
- **Backend API**: See `/backend/` directory
- **Frontend**: See `/frontend/` directory
- **Deployment**: See `/deploy/` directory
- **Docs**: See `/docs/` directory

---

**Status**: 🟢 Production Ready
**Last Updated**: 2026-06-06
**Deployed on**: Windows + Cloudflare Tunnel
