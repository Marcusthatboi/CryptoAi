$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

function Require-Admin {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "[ERROR] This script must be run as Administrator." -ForegroundColor Red
        Write-Host "[INFO] Re-run in elevated PowerShell." -ForegroundColor Yellow
        exit 1
    }
}

function Invoke-TaskCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TaskName,
        [Parameter(Mandatory = $true)]
        [ValidateSet('End','Run')]
        [string]$Action
    )

    $cmd = if ($Action -eq 'End') { "schtasks /End /TN $TaskName" } else { "schtasks /Run /TN $TaskName" }
    Write-Host "[INFO] $cmd"
    cmd /c $cmd | Out-Host
}

function Show-Listener {
    param([int]$Port)

    Write-Host "[INFO] Checking listener on :$Port"
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host "  [WARN] No LISTENING process on :$Port" -ForegroundColor Yellow
        return
    }

    foreach ($item in @($conn)) {
        $pidValue = $item.OwningProcess
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pidValue" -ErrorAction SilentlyContinue
        $name = if ($proc) { $proc.Name } else { 'unknown' }
        Write-Host "  [OK] Port :$Port PID=$pidValue Name=$name"
    }
}

Require-Admin

Write-Host ""
Write-Host "============================================================"
Write-Host " CryptoAI Production Cutover (Windows Tasks)"
Write-Host "============================================================"
Write-Host ""

Write-Host "[STEP 1] Stop stale process families"
Stop-Process -Name cloudflared -Force -ErrorAction SilentlyContinue
Stop-Process -Name node -Force -ErrorAction SilentlyContinue
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

Write-Host "[STEP 2] End startup tasks"
Invoke-TaskCommand -TaskName "CryptoAI-Backend-Startup" -Action "End"
Invoke-TaskCommand -TaskName "CryptoAI-Frontend-Startup" -Action "End"
Invoke-TaskCommand -TaskName "CryptoAI-Tunnel-Startup" -Action "End"
Invoke-TaskCommand -TaskName "CryptoAI-Frontend-Guard" -Action "End"

Start-Sleep -Seconds 2

Write-Host "[STEP 3] Run startup tasks in order"
Invoke-TaskCommand -TaskName "CryptoAI-Backend-Startup" -Action "Run"
Start-Sleep -Seconds 3
Invoke-TaskCommand -TaskName "CryptoAI-Frontend-Startup" -Action "Run"
Start-Sleep -Seconds 3
Invoke-TaskCommand -TaskName "CryptoAI-Tunnel-Startup" -Action "Run"
Start-Sleep -Seconds 2
Invoke-TaskCommand -TaskName "CryptoAI-Frontend-Guard" -Action "Run"

Write-Host "[STEP 4] Listener check"
Show-Listener -Port 8002
Show-Listener -Port 5175

Write-Host ""
Write-Host "[DONE] Cutover command sequence finished."
Write-Host "[NEXT] Run deploy/scripts/verify_public_release.ps1 to validate public endpoints."
