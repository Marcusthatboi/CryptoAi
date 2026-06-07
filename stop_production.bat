@echo off
REM Stop all production services

echo Stopping CryptoAI production services...
taskkill /FI "WINDOWTITLE eq CryptoAI*" /T /F >nul 2>&1

echo.
echo ✅ All services stopped
echo.
pause
