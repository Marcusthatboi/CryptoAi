$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$checks = @(
    @{ Name = 'health'; Url = 'https://api.dacryptobeast.com/health'; Method = 'GET'; ExpectStatuses = @(200) },
    @{ Name = 'price-bitcoin'; Url = 'https://api.dacryptobeast.com/api/price/bitcoin'; Method = 'GET'; ExpectStatuses = @(200) },
    @{ Name = 'price-toncoin'; Url = 'https://api.dacryptobeast.com/api/price/toncoin'; Method = 'GET'; ExpectStatuses = @(200) },
    @{ Name = 'price-polygon'; Url = 'https://api.dacryptobeast.com/api/price/polygon'; Method = 'GET'; ExpectStatuses = @(200) },
    @{ Name = 'promo-status'; Url = 'https://api.dacryptobeast.com/api/promo/status'; Method = 'GET'; ExpectStatuses = @(200) },
    @{ Name = 'verification-status-route'; Url = 'https://api.dacryptobeast.com/api/auth/verification-status'; Method = 'GET'; ExpectStatuses = @(200, 401) },
    @{ Name = 'checkout-session-route'; Url = 'https://api.dacryptobeast.com/api/subscription/create-checkout-session?tier=pro&origin=https%3A%2F%2Fdacryptobeast.com'; Method = 'POST'; ExpectStatuses = @(200, 401, 400) }
)

$failures = @()

Write-Host ""
Write-Host "============================================================"
Write-Host " CryptoAI Public Release Verification"
Write-Host "============================================================"
Write-Host ""

foreach ($item in $checks) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $item.Url -Method $item.Method -TimeoutSec 25 -ErrorAction Stop
        if ($resp.StatusCode -notin $item.ExpectStatuses) {
            $expected = ($item.ExpectStatuses -join ', ')
            $msg = "[FAIL] $($item.Name): expected one of [$expected], got $($resp.StatusCode)"
            $failures += $msg
            Write-Host $msg -ForegroundColor Red
            continue
        }

        Write-Host "[OK] $($item.Name): HTTP $($resp.StatusCode)"

        if ($item.Name -eq 'price-toncoin') {
            $payload = $resp.Content | ConvertFrom-Json
            if ($payload.id -ne 'the-open-network') {
                $msg = "[FAIL] price-toncoin id expected the-open-network, got $($payload.id)"
                $failures += $msg
                Write-Host $msg -ForegroundColor Red
            }
        }

        if ($item.Name -eq 'price-polygon') {
            $payload = $resp.Content | ConvertFrom-Json
            if ($payload.id -ne 'matic-network') {
                $msg = "[FAIL] price-polygon id expected matic-network, got $($payload.id)"
                $failures += $msg
                Write-Host $msg -ForegroundColor Red
            }
        }
    }
    catch {
        $statusCode = 'ERR'
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        if ($statusCode -in $item.ExpectStatuses) {
            Write-Host "[OK] $($item.Name): HTTP $statusCode"
        }
        else {
            $expected = ($item.ExpectStatuses -join ', ')
            $msg = "[FAIL] $($item.Name): expected one of [$expected], got $statusCode"
            $failures += $msg
            Write-Host $msg -ForegroundColor Red
        }
    }
}

try {
    $preflightHeaders = @{
        Origin = 'https://dacryptobeast.com'
        'Access-Control-Request-Method' = 'POST'
        'Access-Control-Request-Headers' = 'authorization,content-type'
    }
    $preflight = Invoke-WebRequest `
        -UseBasicParsing `
        -Uri 'https://api.dacryptobeast.com/auth/login' `
        -Method OPTIONS `
        -Headers $preflightHeaders `
        -TimeoutSec 25 `
        -ErrorAction Stop

    if ($preflight.StatusCode -notin @(200, 204)) {
        $msg = "[FAIL] cors-preflight: expected one of [200, 204], got $($preflight.StatusCode)"
        $failures += $msg
        Write-Host $msg -ForegroundColor Red
    }
    else {
        $allowOrigin = $preflight.Headers['Access-Control-Allow-Origin']
        if (-not $allowOrigin) {
            $msg = "[FAIL] cors-preflight: missing Access-Control-Allow-Origin header"
            $failures += $msg
            Write-Host $msg -ForegroundColor Red
        }
        else {
            Write-Host "[OK] cors-preflight: HTTP $($preflight.StatusCode), ACAO=$allowOrigin"
        }
    }
}
catch {
    $statusCode = 'ERR'
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
    }
    $msg = "[FAIL] cors-preflight: expected one of [200, 204], got $statusCode"
    $failures += $msg
    Write-Host $msg -ForegroundColor Red
}

try {
    $bundle = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $url = "https://dacryptobeast.com/?nocache=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())&attempt=$attempt"
        $html = (Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 25).Content
        $m = [regex]::Match($html, 'index-[A-Za-z0-9_-]+\.js')
        if ($m.Success) {
            $bundle = $m.Value
            break
        }
    }

    if ($bundle) {
        Write-Host "[INFO] bundle: $bundle"
        if ($bundle -eq 'index-C5EER-vF.js') {
            $msg = "[FAIL] Frontend bundle still stale: $bundle"
            $failures += $msg
            Write-Host $msg -ForegroundColor Red
        }
    }
    else {
        $msg = "[FAIL] Could not detect frontend bundle hash"
        $failures += $msg
        Write-Host $msg -ForegroundColor Red
    }
}
catch {
    $msg = "[FAIL] Could not fetch frontend HTML"
    $failures += $msg
    Write-Host $msg -ForegroundColor Red
}

Write-Host ""
if ($failures.Count -eq 0) {
    Write-Host "[PASS] Public release checks passed." -ForegroundColor Green
    exit 0
}

Write-Host "[FAIL] Public release checks failed:" -ForegroundColor Red
$failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
exit 1
