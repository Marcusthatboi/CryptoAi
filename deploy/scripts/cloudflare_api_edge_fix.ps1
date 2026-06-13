param(
    [ValidateSet("verify", "apply")]
    [string]$Mode = "verify",

    [string]$ApiHost = "api.dacryptobeast.com",
    [string]$ExpectedOriginIp = "34.70.44.250",
    [string]$BashPath = "C:\Program Files\Git\bin\bash.exe",

    [switch]$SkipEnvCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-ToBashPath {
    param([Parameter(Mandatory = $true)][string]$WindowsPath)

    $normalized = $WindowsPath.Replace("\\", "/")
    if ($normalized -match "^([A-Za-z]):/(.*)$") {
        $drive = $matches[1].ToLowerInvariant()
        $rest = $matches[2]
        return "/$drive/$rest"
    }

    return $normalized
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$bashScript = Join-Path $repoRoot "deploy\scripts\cloudflare_api_edge_fix.sh"

if (-not (Test-Path $bashScript)) {
    throw "Cannot find Bash script: $bashScript"
}

if (-not (Test-Path $BashPath)) {
    $bashCmd = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashCmd) {
        $BashPath = $bashCmd.Source
    }
    else {
        throw "Bash not found. Install Git Bash or pass -BashPath explicitly."
    }
}

if (-not $SkipEnvCheck) {
    $missing = @()
    if (-not $env:CF_API_TOKEN) { $missing += "CF_API_TOKEN" }
    if (-not $env:CF_ZONE_ID) { $missing += "CF_ZONE_ID" }

    if ($missing.Count -gt 0) {
        throw "Missing required environment variable(s): $($missing -join ', ').`nSet them in this shell before running."
    }
}

$env:API_HOST = $ApiHost
$env:EXPECTED_ORIGIN_IP = $ExpectedOriginIp

$repoRootBash = Convert-ToBashPath -WindowsPath $repoRoot
$bashCommand = "cd '$repoRootBash' && ./deploy/scripts/cloudflare_api_edge_fix.sh $Mode"

Write-Host "Running Cloudflare edge fixer in mode '$Mode'"
Write-Host "Repository: $repoRoot"
Write-Host "Host: $ApiHost"
Write-Host "Expected origin IP: $ExpectedOriginIp"

& $BashPath -lc $bashCommand
exit $LASTEXITCODE
