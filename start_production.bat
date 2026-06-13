@echo off
setlocal

REM CryptoAI Production Startup Script
REM Starts backend, tunnel, and production frontend preview in separate windows.

set "PROJECT_DIR=%~dp0"
set "BACKEND_SCRIPT=%PROJECT_DIR%start_backend.bat"
set "TUNNEL_SCRIPT=%PROJECT_DIR%start_tunnel.bat"
set "FRONTEND_SCRIPT=%PROJECT_DIR%start_frontend.bat"

title CryptoAI Production Suite

echo.
echo ============================================================
echo   CryptoAI Production Startup
echo ============================================================
echo   Backend:  http://127.0.0.1:8002
echo   Frontend: http://127.0.0.1:5175
echo   Public:   https://dacryptobeast.com
echo   API:      https://api.dacryptobeast.com
echo.

if not exist "%BACKEND_SCRIPT%" (
	echo [ERROR] Missing launcher: %BACKEND_SCRIPT%
	exit /b 1
)

if not exist "%TUNNEL_SCRIPT%" (
	echo [ERROR] Missing launcher: %TUNNEL_SCRIPT%
	exit /b 1
)

if not exist "%FRONTEND_SCRIPT%" (
	echo [ERROR] Missing launcher: %FRONTEND_SCRIPT%
	exit /b 1
)

echo [1/3] Starting backend...
start "CryptoAI Backend" /MIN cmd /c "cd /d "%PROJECT_DIR%" && "%BACKEND_SCRIPT%""

echo [2/3] Starting Cloudflare tunnel...
start "CryptoAI Tunnel" /MIN cmd /c "cd /d "%PROJECT_DIR%" && "%TUNNEL_SCRIPT%""

echo [3/3] Starting production frontend preview...
start "CryptoAI Frontend" /MIN cmd /c "cd /d "%PROJECT_DIR%" && "%FRONTEND_SCRIPT%""

echo.
echo Startup commands sent.
echo.
echo Access points:
echo   Frontend (local):   http://127.0.0.1:5175
echo   Frontend (public):  https://dacryptobeast.com
echo   API (local):        http://127.0.0.1:8002
echo   API (public):       https://api.dacryptobeast.com
echo   Health:             https://api.dacryptobeast.com/health
echo.
echo This launcher can be closed after the three service windows start.

exit /b 0
