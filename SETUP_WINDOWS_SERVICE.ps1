$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

Write-Host ""
Write-Host "============================================================================"
Write-Host " CryptoAI Windows Service Setup"
Write-Host "============================================================================"
Write-Host ""
Write-Host "This script will:"
Write-Host "  1. Remove broken Windows service entries"
Write-Host "  2. Create startup Scheduled Tasks for backend/tunnel/frontend"
Write-Host "  3. Start tasks now"
Write-Host "  4. Keep them running automatically after reboot"
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    exit 1
}

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendScript = Join-Path $projectDir 'start_backend.bat'
$tunnelScript = Join-Path $projectDir 'start_tunnel.bat'
$frontendScript = Join-Path $projectDir 'start_frontend.bat'
$frontendGuardScript = Join-Path $projectDir 'deploy\scripts\ensure_frontend_5175.ps1'
$cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
$powershellExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

function Remove-ServiceIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $existing = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if (-not $existing) {
        return
    }

    Write-Host "[INFO] Removing existing service: $Name"
    try {
        Stop-Service -Name $Name -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "[WARN] Could not stop service $Name (continuing)" -ForegroundColor Yellow
    }

    try {
        sc.exe delete $Name | Out-Null
    } catch {
        Write-Host "[WARN] Could not delete service $Name (continuing)" -ForegroundColor Yellow
    }
}

function Remove-TaskIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TaskName

    )

    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $existingTask) {
        return
    }

    Write-Host "[INFO] Removing existing scheduled task: $TaskName"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

function Install-StartupTask {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TaskName,
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,
        [Parameter(Mandatory = $true)]
        [string]$TaskDescription
    )

    if (-not (Test-Path $ScriptPath)) {
        throw "Missing startup script: $ScriptPath"
    }

    $workDir = Split-Path -Parent $ScriptPath
    $cmdArgs = '/c "cd /d ""' + $workDir + '"" && ""' + $ScriptPath + '"""'

    $action = New-ScheduledTaskAction -Execute $cmdExe -Argument $cmdArgs
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -RestartCount 999 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

    Write-Host "[INFO] Task note: $TaskDescription"
}

function Install-RecurringTask {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TaskName,
        [Parameter(Mandatory = $true)]
        [string]$ExecutablePath,
        [Parameter(Mandatory = $true)]
        [string]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$TaskDescription,
        [int]$IntervalMinutes = 5
    )

    if (-not (Test-Path $ExecutablePath)) {
        throw "Missing executable: $ExecutablePath"
    }

    $action = New-ScheduledTaskAction -Execute $ExecutablePath -Argument $Arguments
    $trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Days 3650)
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $TaskDescription -Force | Out-Null
    Write-Host "[INFO] Task note: $TaskDescription"
}

Write-Host "[INFO] Project directory: $projectDir"
Write-Host ""

Write-Host "============================================================================"
Write-Host " Installing Startup Tasks"
Write-Host "============================================================================"
Write-Host ""

$legacyServices = @(
    'CryptoAI-Backend',
    'CryptoAI-Tunnel',
    'CryptoAI-Frontend'
)

foreach ($svc in $legacyServices) {
    Remove-ServiceIfExists -Name $svc
}

$tasks = @(
    @{ Name = 'CryptoAI-Backend-Startup'; Script = $backendScript; Note = 'Runs backend API on startup' },
    @{ Name = 'CryptoAI-Tunnel-Startup'; Script = $tunnelScript; Note = 'Runs Cloudflare tunnel on startup' },
    @{ Name = 'CryptoAI-Frontend-Startup'; Script = $frontendScript; Note = 'Runs frontend server on startup' }
)

foreach ($task in $tasks) {
    Remove-TaskIfExists -TaskName $task.Name
}

foreach ($task in $tasks) {
    Write-Host "[INFO] Installing $($task.Name) task..."
    Install-StartupTask -TaskName $task.Name -ScriptPath $task.Script -TaskDescription $task.Note

    Write-Host "[OK] $($task.Name) installed"
}

$frontendGuardTaskName = 'CryptoAI-Frontend-Guard'
Remove-TaskIfExists -TaskName $frontendGuardTaskName

Write-Host "[INFO] Installing $frontendGuardTaskName task..."
Install-RecurringTask `
    -TaskName $frontendGuardTaskName `
    -ExecutablePath $powershellExe `
    -Arguments ('-NoProfile -ExecutionPolicy Bypass -File "' + $frontendGuardScript + '"') `
    -TaskDescription 'Checks every 5 minutes and restarts frontend startup task if port 5175 is down' `
    -IntervalMinutes 5
Write-Host "[OK] $frontendGuardTaskName installed"

Write-Host ""
Write-Host "============================================================================"
Write-Host " Starting Tasks"
Write-Host "============================================================================"
Write-Host ""

foreach ($task in $tasks) {
    Write-Host "[INFO] Starting $($task.Name)..."
    try {
        Start-ScheduledTask -TaskName $task.Name -ErrorAction Stop
        Write-Host "[OK] $($task.Name) started"
    } catch {
        Write-Host "[WARN] $($task.Name) failed to start" -ForegroundColor Yellow
    }
}

Write-Host "[INFO] Starting $frontendGuardTaskName..."
try {
    Start-ScheduledTask -TaskName $frontendGuardTaskName -ErrorAction Stop
    Write-Host "[OK] $frontendGuardTaskName started"
}
catch {
    Write-Host "[WARN] $frontendGuardTaskName failed to start" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================================"
Write-Host " Verification"
Write-Host "============================================================================"
Write-Host ""

foreach ($task in $tasks) {
    $registered = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
    if (-not $registered) {
        Write-Host "$($task.Name): not found"
        continue
    }

    $info = Get-ScheduledTaskInfo -TaskName $task.Name
    Write-Host "$($task.Name): Status: $($registered.State), LastRun: $($info.LastRunTime), LastResult: $($info.LastTaskResult)"
}

$guardRegistered = Get-ScheduledTask -TaskName $frontendGuardTaskName -ErrorAction SilentlyContinue
if ($guardRegistered) {
    $guardInfo = Get-ScheduledTaskInfo -TaskName $frontendGuardTaskName
    Write-Host "${frontendGuardTaskName}: Status: $($guardRegistered.State), LastRun: $($guardInfo.LastRunTime), LastResult: $($guardInfo.LastTaskResult)"
} else {
    Write-Host "${frontendGuardTaskName}: not found"
}

Write-Host ""
Write-Host "============================================================================"
Write-Host " Setup Complete"
Write-Host "============================================================================"
Write-Host ""
Write-Host "Startup tasks installed and set to run on boot."
Write-Host ""
Write-Host "Verify with:"
Write-Host "  schtasks.exe /Query /TN CryptoAI-Backend-Startup /FO LIST /V"
Write-Host "  schtasks.exe /Query /TN CryptoAI-Tunnel-Startup /FO LIST /V"
Write-Host "  schtasks.exe /Query /TN CryptoAI-Frontend-Startup /FO LIST /V"
Write-Host "  schtasks.exe /Query /TN CryptoAI-Frontend-Guard /FO LIST /V"

exit 0
