@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "TARGET=%SCRIPT_DIR%SETUP_WINDOWS_SERVICE.bat"

if not exist "%TARGET%" (
  echo [ERROR] Missing installer: %TARGET%
  pause
  exit /b 1
)

echo Launching elevated installer...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/k','""%TARGET%""' -Verb RunAs"

if errorlevel 1 (
  echo [ERROR] Could not request Administrator elevation.
  echo Try opening Windows Terminal as Administrator and run:
  echo   cd /d "%SCRIPT_DIR%"
  echo   SETUP_WINDOWS_SERVICE.bat
  pause
  exit /b 1
)

echo [INFO] UAC prompt sent. Approve it to continue installation.
echo [INFO] The elevated installer opens in a new window and stays open when finished.
echo [INFO] You can close this launcher window.
exit /b 0
