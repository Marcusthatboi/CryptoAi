# Final Delivery Control Sheet (Execution)

Last updated: 2026-06-11
Release target: Final Delivery Candidate
Current decision: NO-GO (until P0 closes)

## Live Baseline (Captured)

- [x] API health is reachable: `GET https://api.dacryptobeast.com/health` => 200
- [ ] Public price endpoints healthy:
  - `GET https://api.dacryptobeast.com/api/price/bitcoin` => 404
  - `GET https://api.dacryptobeast.com/api/price/toncoin` => 404
  - `GET https://api.dacryptobeast.com/api/price/polygon` => 404
- [ ] Frontend bundle updated on production: currently `index-C5EER-vF.js` (stale)

## P0 (Blockers) - Must Close Before GO

- [ ] **P0-1: Eliminate stale runtime connectors and unify production path**
  - Owner: DevOps Lead
  - Deadline: 2026-06-12 14:00 UTC
  - Definition of done:
    - Only one active backend runtime serving `api.dacryptobeast.com`
    - Only one active frontend runtime serving `dacryptobeast.com`
    - No stale SYSTEM tunnel connectors routing old code
  - Evidence required:
    - `cloudflared tunnel info dacryptobeast-root`
    - `netstat` listeners for 8002 and 5175
    - Public endpoint re-check screenshots/logs

- [ ] **P0-2: Deploy fixed backend routing behavior to production runtime**
  - Owner: Backend Lead
  - Deadline: 2026-06-12 15:00 UTC
  - Definition of done:
    - `GET /api/price/bitcoin` => 200
    - `GET /api/price/toncoin` => 200 with `id=the-open-network`
    - `GET /api/price/polygon` => 200 with `id=matic-network`
  - Evidence required:
    - Terminal output of public endpoint calls

- [ ] **P0-3: Deploy current frontend build to production path**
  - Owner: Frontend Lead
  - Deadline: 2026-06-12 16:00 UTC
  - Definition of done:
    - Production HTML references new hash (not `index-C5EER-vF.js`)
    - Browser hard refresh shows updated bundle
  - Evidence required:
    - `Invoke-WebRequest https://dacryptobeast.com` hash extraction output

- [ ] **P0-4: Release governance assignment and sign-off ownership**
  - Owner: Product Manager
  - Deadline: 2026-06-12 16:30 UTC
  - Definition of done:
    - Named release owner
    - Named Engineering/Product/Operations approvers
    - Approved cutover window

## P1 (Critical Validation) - Complete Within 48h

- [ ] **P1-1: Payment production readiness validation**
  - Owner: Payments Engineer + QA Lead
  - Deadline: 2026-06-13 14:00 UTC
  - Checklist:
    - Live/test key alignment confirmed
    - Webhook signature validation tested
    - Upgrade success/cancel/failure flows passed
    - Apple Pay domain/device verification completed

- [ ] **P1-2: Trading safety E2E validation**
  - Owner: Trading Integrations Engineer + QA Lead
  - Deadline: 2026-06-13 16:00 UTC
  - Checklist:
    - Real trade precheck ready
    - Small-value live trade test completed
    - Payment-success/trade-failure compensation path tested

- [ ] **P1-3: Portfolio integrity and accounting validation**
  - Owner: Backend Lead + Data QA
  - Deadline: 2026-06-13 18:00 UTC
  - Checklist:
    - Fake vs real totals correct
    - Realized/unrealized P&L correct
    - Buying power persistence verified after refresh
    - No transaction loss in activity log

## P2 (Operational Hardening) - Complete Within 5 Days

- [ ] **P2-1: Monitoring and alerting verification**
  - Owner: SRE/Operations
  - Deadline: 2026-06-16 14:00 UTC
  - Checklist:
    - 5xx alerting active
    - Webhook failure alerting active
    - Trade execution failure alerting active

- [ ] **P2-2: Rollback drill execution**
  - Owner: DevOps Lead + Incident Commander
  - Deadline: 2026-06-16 16:00 UTC
  - Checklist:
    - Timed rollback drill executed
    - Recovery validation documented

## Execution Commands (Operations)

Preferred execution path (faster and repeatable):

```powershell
# Run elevated
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\cutover_windows_services.ps1

# Run verification
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\verify_public_release.ps1
```

Manual command path:

Run in elevated PowerShell on production host:

```powershell
Stop-Process -Name cloudflared -Force -ErrorAction SilentlyContinue
Stop-Process -Name node -Force -ErrorAction SilentlyContinue
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

schtasks /End /TN CryptoAI-Backend-Startup
schtasks /End /TN CryptoAI-Frontend-Startup
schtasks /End /TN CryptoAI-Tunnel-Startup

Start-Sleep -Seconds 2

schtasks /Run /TN CryptoAI-Backend-Startup
Start-Sleep -Seconds 3
schtasks /Run /TN CryptoAI-Frontend-Startup
Start-Sleep -Seconds 3
schtasks /Run /TN CryptoAI-Tunnel-Startup
```

Verification commands:

```powershell
Invoke-RestMethod https://api.dacryptobeast.com/health
Invoke-RestMethod https://api.dacryptobeast.com/api/price/bitcoin
Invoke-RestMethod https://api.dacryptobeast.com/api/price/toncoin
Invoke-RestMethod https://api.dacryptobeast.com/api/price/polygon
(Invoke-WebRequest https://dacryptobeast.com).Content | Select-String "index-[A-Za-z0-9_-]+.js"
```

## GO Criteria

- [ ] All P0 tasks closed with evidence
- [ ] No failing public price endpoint in smoke set
- [ ] Frontend bundle hash updated on public domain
- [ ] Release owner and approvers signed
- [ ] P1 tasks scheduled and in-progress with named owners
