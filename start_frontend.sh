#!/bin/bash
# Start only the React Frontend

echo ""
echo "====================================================="
echo "  CryptoAI Frontend Dashboard"
echo "====================================================="
echo ""

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "Starting React development server..."
echo "Dashboard running on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd frontend
npm run dev
cd ..
