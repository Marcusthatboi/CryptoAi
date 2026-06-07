param(
  [switch]$UseHA = $true,
  [switch]$Build = $true
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../.."

$composeFile = if ($UseHA) { "docker-compose.ha.yml" } else { "docker-compose.prod.yml" }
$buildArg = if ($Build) { "--build" } else { "" }

Write-Host "Using compose file: $composeFile"

if (-not (Test-Path ".env")) {
  throw "Missing .env file. Copy .env.example to .env and configure secrets first."
}

docker compose -f $composeFile up $buildArg -d

docker compose -f $composeFile ps
Write-Host "Deployment completed."
