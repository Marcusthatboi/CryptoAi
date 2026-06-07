param(
  [string]$BaseUrl = "http://127.0.0.1:8002",
  [string]$FrontendUrl = "http://127.0.0.1:8080"
)

$ErrorActionPreference = "Stop"

function Test-Endpoint {
  param(
    [string]$Name,
    [string]$Url
  )

  $attempts = 0
  $maxAttempts = 3
  $lastError = $null

  while ($attempts -lt $maxAttempts) {
    $attempts++
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 8
      return [PSCustomObject]@{
        component = $Name
        status = "UP"
        code = $response.StatusCode
        url = $Url
        timestamp = (Get-Date).ToString("s")
      }
    }
    catch {
      $lastError = $_.Exception.Message
      Start-Sleep -Milliseconds 500
    }
  }

  [PSCustomObject]@{
    component = $Name
    status = "DOWN"
    code = "n/a"
    url = $Url
    timestamp = (Get-Date).ToString("s")
    error = $lastError
  }
}

$checks = @()
$checks += Test-Endpoint -Name "backend-health" -Url "$BaseUrl/health"
$checks += Test-Endpoint -Name "backend-root" -Url "$BaseUrl/"
$checks += Test-Endpoint -Name "frontend" -Url $FrontendUrl

$checks | Format-Table -AutoSize

if ($checks.status -contains "DOWN") {
  exit 1
}
