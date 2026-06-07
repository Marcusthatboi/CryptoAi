#!/bin/bash
# Start CryptoAI Web Application
# This script starts both the FastAPI backend and React frontend

echo ""
echo "====================================================="
echo "  CryptoAI Web Application Startup"
echo "====================================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating Python virtual environment..."
source .venv/bin/activate

# Support email defaults (set SMTP credentials before sending works)
export SUPPORT_EMAIL_TO="${SUPPORT_EMAIL_TO:-cryptosupport74@gmail.com}"
export SUPPORT_SMTP_HOST="${SUPPORT_SMTP_HOST:-smtp.gmail.com}"
export SUPPORT_SMTP_PORT="${SUPPORT_SMTP_PORT:-587}"
export SUPPORT_SMTP_USE_TLS="${SUPPORT_SMTP_USE_TLS:-true}"

if [ -z "$SUPPORT_SMTP_USERNAME" ]; then
    echo "[WARN] SUPPORT_SMTP_USERNAME is not set. Support form emails will fail."
fi

if [ -z "$SUPPORT_SMTP_PASSWORD" ]; then
    echo "[WARN] SUPPORT_SMTP_PASSWORD is not set. Use a Gmail App Password."
fi

# Check if backend dependencies are installed
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "====================================================="
echo "  Starting Services"
echo "====================================================="
echo ""
echo "Backend will start on:  http://localhost:8002"
echo "Frontend will start on: http://localhost:3000"
echo "API Docs:              http://localhost:8002/docs"
echo "Support inbox:         $SUPPORT_EMAIL_TO"
echo ""
echo "Press Ctrl+C to stop services"
echo ""

# Start backend in background
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend
cd frontend
npm run dev
cd ..

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
