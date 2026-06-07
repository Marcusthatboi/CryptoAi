@echo off
REM Start only the CryptoAI Backend API

echo.
echo =====================================================
echo   CryptoAI Backend API
echo =====================================================
echo.

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .\.venv\Scripts\activate.bat

REM Support email defaults (set SMTP credentials before sending works)
if "%SUPPORT_EMAIL_TO%"=="" set SUPPORT_EMAIL_TO=cryptosupport74@gmail.com
if "%SUPPORT_SMTP_HOST%"=="" set SUPPORT_SMTP_HOST=smtp.gmail.com
if "%SUPPORT_SMTP_PORT%"=="" set SUPPORT_SMTP_PORT=587
if "%SUPPORT_SMTP_USE_TLS%"=="" set SUPPORT_SMTP_USE_TLS=true

if "%SUPPORT_SMTP_USERNAME%"=="" (
    echo.
    echo [WARN] SUPPORT_SMTP_USERNAME is not set.
    echo [WARN] Support form emails will fail until SMTP credentials are configured.
)

if "%SUPPORT_SMTP_PASSWORD%"=="" (
    echo [WARN] SUPPORT_SMTP_PASSWORD is not set.
    echo [WARN] Use a Gmail App Password when SMTP host is gmail.
    echo.
)

REM Set environment for local development
set "APP_ENV=development"
set "FRONTEND_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5176,https://dacryptobeast.com,https://www.dacryptobeast.com"

echo [INFO] APP_ENV: %APP_ENV%
echo [INFO] CORS Origins configured for development

pip show fastapi > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting FastAPI backend...
echo API running on: http://localhost:8002
echo API docs:       http://localhost:8002/docs
echo Support inbox:  %SUPPORT_EMAIL_TO%
echo.
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
