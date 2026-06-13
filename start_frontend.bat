REM Start only the React Frontend

echo.
echo =====================================================
echo   CryptoAI Frontend Dashboard
echo =====================================================
echo.

REM Ensure stale preview processes do not keep serving old bundles.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5175" ^| findstr "LISTENING"') do (
    echo [INFO] Stopping existing listener on port 5175 ^(PID %%p^)...
    taskkill /PID %%p /F >nul 2>&1
)

if not exist "frontend\node_modules" (
    echo Installing dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo Building production frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed.
    exit /b 1
)

echo.
echo Starting production preview server...
echo Dashboard running on: http://127.0.0.1:5175
echo.
echo Press Ctrl+C to stop
echo.

call npm run preview:prod
cd ..
