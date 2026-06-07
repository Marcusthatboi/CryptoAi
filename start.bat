@echo off
REM Start CryptoAI Web Application
REM This script starts both the FastAPI backend and React frontend

echo.
echo =====================================================
echo   CryptoAI Web Application Startup
echo =====================================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating Python virtual environment...
call .\.venv\Scripts\activate.bat

REM Support email defaults (set SMTP credentials before sending works)
if "%SUPPORT_EMAIL_TO%"=="" set SUPPORT_EMAIL_TO=cryptosupport74@gmail.com
if "%SUPPORT_SMTP_HOST%"=="" set SUPPORT_SMTP_HOST=smtp.gmail.com
if "%SUPPORT_SMTP_PORT%"=="" set SUPPORT_SMTP_PORT=587
if "%SUPPORT_SMTP_USE_TLS%"=="" set SUPPORT_SMTP_USE_TLS=true

if "%SUPPORT_SMTP_USERNAME%"=="" (
    echo [WARN] SUPPORT_SMTP_USERNAME is not set. Support form emails will fail.
)

if "%SUPPORT_SMTP_PASSWORD%"=="" (
    echo [WARN] SUPPORT_SMTP_PASSWORD is not set. Use a Gmail App Password.
)

REM Check if backend dependencies are installed
pip show fastapi > nul 2>&1
if errorlevel 1 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

echo.
echo =====================================================
echo   Starting Services
echo =====================================================
echo.
echo Backend will start on:  http://localhost:8002
echo Frontend will start on: http://localhost:3000
echo API Docs:              http://localhost:8002/docs
echo Support inbox:         %SUPPORT_EMAIL_TO%
echo.
echo Press Ctrl+C to stop both services
echo.

REM Start backend in a new window
start "CryptoAI Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 --reload"

REM Wait a moment for backend to start
timeout /t 2 /nobreak

REM Start frontend
cd frontend
npm run dev
cd ..
