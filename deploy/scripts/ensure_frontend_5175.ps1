$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$frontendTaskName = 'CryptoAI-Frontend-Startup'

try {
    $listener = Get-NetTCPConnection -LocalPort 5175 -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        exit 0
    }

    Write-Host "[WARN] No frontend listener on :5175. Starting $frontendTaskName"
    Start-ScheduledTask -TaskName $frontendTaskName -ErrorAction Stop
    exit 0
}
catch {
    Write-Host "[ERROR] Frontend guard failed: $($_.Exception.Message)"
    exit 1
}
