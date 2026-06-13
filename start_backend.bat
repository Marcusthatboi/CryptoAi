@echo off
REM Start only the CryptoAI Backend API

echo.
echo =====================================================
echo   CryptoAI Backend API
echo =====================================================
echo.

REM Kill any existing non-privileged python process on 8002 so updated code loads.
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8002" ^| findstr "LISTENING"') do (
    echo [INFO] Stopping existing backend process PID %%a
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

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

REM Preserve .env values when set; otherwise apply sane production-oriented defaults.
if "%APP_ENV%"=="" set "APP_ENV=production"
if "%ENVIRONMENT%"=="" set "ENVIRONMENT=%APP_ENV%"
if "%FRONTEND_ALLOWED_ORIGINS%"=="" set "FRONTEND_ALLOWED_ORIGINS=https://dacryptobeast.com,https://www.dacryptobeast.com,http://127.0.0.1:5175,http://localhost:5175"

echo [INFO] APP_ENV: %APP_ENV%
echo [INFO] ENVIRONMENT: %ENVIRONMENT%
echo [INFO] FRONTEND_ALLOWED_ORIGINS: %FRONTEND_ALLOWED_ORIGINS%

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
