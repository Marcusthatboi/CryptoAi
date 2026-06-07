@echo off
REM ============================================================================
REM  CryptoAI Windows Service Setup
REM  Run this script as Administrator to install/start services
REM ============================================================================

echo.
echo ============================================================================
echo  CryptoAI Windows Service Setup
echo ============================================================================
echo.
echo This script will:
echo   1. Download NSSM (Non-Sucking Service Manager) if needed
echo   2. Create Windows Service for Backend API
echo   3. Create Windows Service for Frontend
echo   4. Start services automatically on boot
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

set "PROJECT_DIR=%~dp0"
set "BACKEND_SCRIPT=%PROJECT_DIR%start_backend.bat"
set "FRONTEND_SCRIPT=%PROJECT_DIR%start_frontend.bat"
set "NSSM_DIR=%PROJECT_DIR%.nssm"
set "NSSM_EXE=%NSSM_DIR%\nssm.exe"

echo [INFO] Project directory: %PROJECT_DIR%
echo.

REM Download NSSM if needed
if not exist "%NSSM_EXE%" (
    echo [INFO] Downloading NSSM (Non-Sucking Service Manager)...
    if not exist "%NSSM_DIR%" mkdir "%NSSM_DIR%"
    
    REM Download 32-bit NSSM
    powershell -Command "& {(New-Object System.Net.WebClient).DownloadFile('https://nssm.cc/download/nssm-2.24-101-g897c7ad.zip', '%NSSM_DIR%\nssm.zip')}"
    
    if not exist "%NSSM_DIR%\nssm.zip" (
        echo [ERROR] Failed to download NSSM
        echo Download manually from https://nssm.cc/ and extract to: %NSSM_DIR%
        pause
        exit /b 1
    )
    
    echo [INFO] Extracting NSSM...
    powershell -Command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%NSSM_DIR%\nssm.zip', '%NSSM_DIR%')}"
    
    REM Move nssm.exe to expected location
    for /d %%D in ("%NSSM_DIR%\nssm-*") do (
        copy "%%D\win32\nssm.exe" "%NSSM_EXE%" >nul
        if exist "%%D\nssm.exe" copy "%%D\nssm.exe" "%NSSM_EXE%" >nul
    )
    
    if not exist "%NSSM_EXE%" (
        echo [ERROR] Could not locate nssm.exe after extraction
        pause
        exit /b 1
    )
    
    echo [OK] NSSM installed
)

echo.
echo ============================================================================
echo  Installing Services
echo ============================================================================
echo.

REM Stop existing services if they exist
echo [INFO] Stopping existing services...
"%NSSM_EXE%" stop CryptoAI-Backend >nul 2>&1
"%NSSM_EXE%" stop CryptoAI-Frontend >nul 2>&1
timeout /t 2 /nobreak >nul

REM Remove existing services
echo [INFO] Removing existing services...
"%NSSM_EXE%" remove CryptoAI-Backend confirm >nul 2>&1
"%NSSM_EXE%" remove CryptoAI-Frontend confirm >nul 2>&1
timeout /t 2 /nobreak >nul

REM Create Backend Service
echo [INFO] Installing Backend API service...
"%NSSM_EXE%" install CryptoAI-Backend "%BACKEND_SCRIPT%"
if errorlevel 1 (
    echo [ERROR] Failed to install backend service
    pause
    exit /b 1
)

echo [INFO] Configuring Backend service...
"%NSSM_EXE%" set CryptoAI-Backend AppDirectory "%PROJECT_DIR%"
"%NSSM_EXE%" set CryptoAI-Backend AppNoConsole 0
"%NSSM_EXE%" set CryptoAI-Backend Type SERVICE_WIN32_OWN_PROCESS
"%NSSM_EXE%" set CryptoAI-Backend Start SERVICE_AUTO_START
"%NSSM_EXE%" set CryptoAI-Backend Priority NORMAL_PRIORITY_CLASS
echo [OK] Backend service installed

echo.

REM Create Frontend Service
echo [INFO] Installing Frontend service...
"%NSSM_EXE%" install CryptoAI-Frontend "%FRONTEND_SCRIPT%"
if errorlevel 1 (
    echo [ERROR] Failed to install frontend service
    pause
    exit /b 1
)

echo [INFO] Configuring Frontend service...
"%NSSM_EXE%" set CryptoAI-Frontend AppDirectory "%PROJECT_DIR%"
"%NSSM_EXE%" set CryptoAI-Frontend AppNoConsole 0
"%NSSM_EXE%" set CryptoAI-Frontend Type SERVICE_WIN32_OWN_PROCESS
"%NSSM_EXE%" set CryptoAI-Frontend Start SERVICE_AUTO_START
"%NSSM_EXE%" set CryptoAI-Frontend Priority NORMAL_PRIORITY_CLASS
echo [OK] Frontend service installed

echo.
echo ============================================================================
echo  Starting Services
echo ============================================================================
echo.

echo [INFO] Starting Backend service...
"%NSSM_EXE%" start CryptoAI-Backend
if errorlevel 1 (
    echo [WARN] Backend service failed to start
    echo Check: services.msc for errors
) else (
    echo [OK] Backend service started
)

timeout /t 3 /nobreak >nul

echo [INFO] Starting Frontend service...
"%NSSM_EXE%" start CryptoAI-Frontend
if errorlevel 1 (
    echo [WARN] Frontend service failed to start
    echo Check: services.msc for errors
) else (
    echo [OK] Frontend service started
)

echo.
echo ============================================================================
echo  Verification
echo ============================================================================
echo.

timeout /t 3 /nobreak >nul

echo [INFO] Checking service status...
"%NSSM_EXE%" status CryptoAI-Backend
"%NSSM_EXE%" status CryptoAI-Frontend

echo.
echo ============================================================================
echo  Setup Complete!
echo ============================================================================
echo.
echo Services installed and set to auto-start on boot.
echo.
echo To manage services:
echo   - Open: services.msc (Windows Services Manager)
echo   - Search for: CryptoAI-Backend and CryptoAI-Frontend
echo.
echo To uninstall services:
echo   Run (as Administrator):
echo   "%NSSM_EXE%" remove CryptoAI-Backend confirm
echo   "%NSSM_EXE%" remove CryptoAI-Frontend confirm
echo.
echo To view service logs:
echo   Check Application and Services Logs in Event Viewer
echo.

pause
