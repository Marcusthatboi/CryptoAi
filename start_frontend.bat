REM Start only the React Frontend

echo.
echo =====================================================
echo   CryptoAI Frontend Dashboard
echo =====================================================
echo.

if not exist "frontend\node_modules" (
    echo Installing dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo Starting React development server...
echo Dashboard running on: http://localhost:3000
echo.
echo Press Ctrl+C to stop
echo.

cd frontend
call npm run dev
cd ..
