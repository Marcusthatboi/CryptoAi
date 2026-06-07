#!/bin/bash
# Start only the CryptoAI Backend API

echo ""
echo "====================================================="
echo "  CryptoAI Backend API"
echo "====================================================="
echo ""

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Support email defaults (set SMTP credentials before sending works)
export SUPPORT_EMAIL_TO="${SUPPORT_EMAIL_TO:-cryptosupport74@gmail.com}"
export SUPPORT_SMTP_HOST="${SUPPORT_SMTP_HOST:-smtp.gmail.com}"
export SUPPORT_SMTP_PORT="${SUPPORT_SMTP_PORT:-587}"
export SUPPORT_SMTP_USE_TLS="${SUPPORT_SMTP_USE_TLS:-true}"

if [ -z "$SUPPORT_SMTP_USERNAME" ]; then
    echo "[WARN] SUPPORT_SMTP_USERNAME is not set."
    echo "[WARN] Support form emails will fail until SMTP credentials are configured."
fi

if [ -z "$SUPPORT_SMTP_PASSWORD" ]; then
    echo "[WARN] SUPPORT_SMTP_PASSWORD is not set."
    echo "[WARN] Use a Gmail App Password when SMTP host is gmail."
fi

if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting FastAPI backend..."
echo "API running on: http://localhost:8002"
echo "API docs:       http://localhost:8002/docs"
echo "Support inbox:  $SUPPORT_EMAIL_TO"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
