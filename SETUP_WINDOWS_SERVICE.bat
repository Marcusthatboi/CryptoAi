@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%SETUP_WINDOWS_SERVICE.ps1"

if not exist "%PS_SCRIPT%" (
  echo [ERROR] Missing installer script: %PS_SCRIPT%
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [ERROR] Service setup failed with exit code %EXIT_CODE%.
  echo [INFO] Press any key to close.
  pause >nul
  exit /b %EXIT_CODE%
)

echo.
echo [OK] Service setup completed.
echo [INFO] Press any key to close.
pause >nul

exit /b %EXIT_CODE%
