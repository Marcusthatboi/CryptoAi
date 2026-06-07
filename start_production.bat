@echo off
REM CryptoAI Production Startup Script
REM Starts backend, tunnel, and frontend in separate windows

title CryptoAI Production Suite

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        CryptoAI Production Startup                          ║
echo ║  Backend: http://127.0.0.1:8002                            ║
echo ║  Public:  https://dacryptobeast.com                        ║
echo ║  API:     https://api.dacryptobeast.com                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Start Backend API
echo [1/3] Starting Backend API on port 8002...
start "CryptoAI Backend" /MIN cmd /k "cd /d C:\Users\marcu\CryproAI && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 --reload"
timeout /t 2 /nobreak

REM Start Cloudflare Tunnel
echo [2/3] Starting Cloudflare Tunnel...
start "CryptoAI Tunnel" /MIN cmd /k "cloudflared tunnel run dacryptobeast-root"
timeout /t 2 /nobreak

REM Start Frontend Dev Server
echo [3/3] Starting Frontend Dev Server on port 5173...
start "CryptoAI Frontend" /MIN cmd /k "cd /d C:\Users\marcu\CryproAI\frontend && npm run dev"
timeout /t 2 /nobreak

echo.
echo ✅ All services starting...
echo.
echo 📊 Access points:
echo   • Frontend (dev):     http://localhost:5174
echo   • Frontend (public):  https://dacryptobeast.com
echo   • API (public):       https://api.dacryptobeast.com
echo   • API Docs:           https://api.dacryptobeast.com/docs
echo   • Health Check:       https://api.dacryptobeast.com/health
echo.
echo ℹ️  Leave this window open. Services run in minimized windows.
echo.
pause
