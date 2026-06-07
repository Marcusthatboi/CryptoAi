param(
  [switch]$SecurityScan,
  [switch]$IncludeBuild
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../.."

Write-Host "Running backend test suite..."
python -m unittest discover -s tests -t . -p "test_*.py" -v

if ($IncludeBuild) {
  Write-Host "Running frontend production build..."
  Push-Location frontend
  npm run build
  Pop-Location
}

if ($SecurityScan) {
  Write-Host "Running backend dependency security scan..."
  python -m pip_audit

  Write-Host "Running frontend dependency security scan..."
  Push-Location frontend
  npm audit --omit=dev --audit-level=high
  Pop-Location
}

Write-Host "Maintenance checks completed successfully."
