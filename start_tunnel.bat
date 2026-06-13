@echo off
REM Start only the Cloudflare Tunnel for public API routing

echo.
echo =====================================================
echo   CryptoAI Cloudflare Tunnel
echo =====================================================
echo.

set "CF_EXE=C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not exist "%CF_EXE%" (
    for /f "delims=" %%I in ('where cloudflared 2^>nul') do set "CF_EXE=%%I"
)

if not exist "%CF_EXE%" (
    echo [ERROR] cloudflared is not installed or not in PATH.
    echo Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    exit /b 1
)

set "CF_CONFIG=C:\Users\marcu\.cloudflared\config.yml"

REM If tunnel already has an active Cloudflare connection, skip duplicate startup.
"%CF_EXE%" tunnel info dacryptobeast-root 2>nul | findstr /I "active connection" >nul
if not errorlevel 1 (
    echo [INFO] dacryptobeast-root already has an active connection. Skipping duplicate start.
    exit /b 0
)

REM A stale cloudflared process may exist without active connections.
tasklist /FI "IMAGENAME eq cloudflared.exe" | findstr /I "cloudflared.exe" >nul
if not errorlevel 1 (
    echo [WARN] cloudflared process found, but tunnel is not active. Starting a fresh tunnel process.
)

echo Starting Cloudflare tunnel: dacryptobeast-root
echo Press Ctrl+C to stop
echo.

if exist "%CF_CONFIG%" (
    "%CF_EXE%" --config "%CF_CONFIG%" tunnel run dacryptobeast-root
) else (
    "%CF_EXE%" tunnel run dacryptobeast-root
)
