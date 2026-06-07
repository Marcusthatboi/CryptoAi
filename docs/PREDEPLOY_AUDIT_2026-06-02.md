# Pre-Deployment Audit Report (2026-06-02)

This report executes the release checklist in docs/RELEASE_GO_NO_GO_CHECKLIST.md and records current go/no-go status.

## Final Decision

- NO-GO

Reason: Critical gate failures remain in environment readiness, automated tests, and security audit remediation.

## Gate 1 - Critical Security and Config

- FAIL: No placeholder/test secrets in active runtime config.
  - Evidence: active env scans show test Stripe keys and placeholder-style provider values in local env files.
- FAIL: Frontend production API/WS env vars present and configured.
  - Evidence: frontend env scan found Stripe publishable key, but no VITE_API_BASE_URL or VITE_WS_URL entries in frontend env files.
- PASS (code-level): CORS enforcement uses explicit origin allow list from FRONTEND_ALLOWED_ORIGINS with middleware restriction.
  - Evidence: backend/main.py origin normalization and allow_origins wiring.
- FAIL (runtime-config dependent): Stripe webhook secret configured and signature validation enabled in deployed environment.
  - Evidence: webhook verification exists in code, but live env values were not validated as production-ready in this audit.
- FAIL: Production strict mode confirmed in active runtime env.
  - Evidence: APP_ENV/ENVIRONMENT production flags are present in .env.example, but not confirmed in active env scan.

## Gate 2 - Payments and Apple Pay Readiness

- FAIL: Stripe live/test alignment verified for deployment target.
  - Evidence: active local config indicates test-mode Stripe key usage; production alignment not verified.
- FAIL: Upgrade checkout success/failure/cancel validated on deployment target.
  - Evidence: no end-to-end deployment-environment payment run in this audit.
- FAIL: Apple Pay domain verification completed in Stripe for deployed domain.
  - Evidence: external Stripe dashboard verification not provided in this environment.
- FAIL: Apple Pay tested on Safari + Wallet over HTTPS for deployed domain.
  - Evidence: device/browser validation not executable in this CLI-only audit.

## Gate 3 - Trading Safety

- FAIL: Real trade precheck ready in deployment target.
  - Evidence: not validated against deployed runtime in this audit.
- FAIL: Small-value real trade test completed.
  - Evidence: no live provider trade execution was performed during this audit.
- FAIL: Payment success + trade failure compensation path tested.
  - Evidence: not executed in this audit run.
- PASS (UI/code-level): execution provider readiness states are implemented and shown in frontend flow.
  - Evidence: InvestmentTypeSelector provider readiness and gating logic present.

## Gate 4 - Portfolio and Data Integrity

- FAIL: Sold-position P/L and total correctness revalidated in deployment target.
- FAIL: Fake/real totals separation revalidated in deployment target.
- FAIL: Buying power persistence revalidated after refresh in deployment target.
- FAIL: Activity/data-loss regression revalidated in deployment target.

Note: these were previously implemented, but were not re-executed as production validation in this audit session.

## Gate 5 - Runtime Reliability

- PASS: Backend health endpoint responds.
  - Evidence: TestClient GET /health returned 200 and healthy payload.
- FAIL: Frontend loads without console errors on initial route in deployment target.
  - Evidence: browser-based production route validation not executed in this audit.
- PASS (app-level): websocket connect/disconnect succeeds.
  - Evidence: TestClient websocket_connect('/ws') succeeded and logged connect/disconnect.
- FAIL: Logs/alerts configured for 5xx, webhook, and trade-execution failures.
  - Evidence: alerting pipeline configuration not validated in this audit.

## Gate 6 - Build, Test, Security, Rollback

- PASS: Frontend production build.
  - Evidence: npm run build completed successfully.
- FAIL: Backend tests.
  - Evidence: pytest tests run produced 8 failures and 11 passes (tests/ suite).
  - Major failure signatures:
    - admin customer routes: missing/invalid query params fields and usage counter fields.
    - auth route tests: event loop closed and profile route mismatch.
    - usage summary test: missing usage_counters_total path.
- FAIL: Security scan gates reviewed and remediated.
  - Evidence:
    - pip-audit: urllib3 vulnerability set reported with fixed versions available.
    - npm audit: vulnerabilities reported (including critical) with upgrade path requiring dependency updates.
- PARTIAL: Rollback policy documented, but validation drill evidence not captured in this audit.
  - Evidence: rollback policy exists in docs/RELEASE_SCHEDULE.md; no rollback simulation evidence logged.

## Commands Executed (Audit Evidence)

- frontend build: npm run build
- backend compile: python -m compileall -q backend
- tests: python -m pytest -q tests
- python audit: python -m pip_audit
- npm audit: npm audit --audit-level=high
- app-level health probe: FastAPI TestClient GET /health
- app-level websocket probe: FastAPI TestClient websocket_connect('/ws')

## Required Remediation Before GO

1. Configure production env with live Stripe keys/webhook secret and explicit production frontend API/WS URLs.
2. Resolve failing tests in tests/ suite and re-run until fully green.
3. Remediate dependency vulnerabilities:
   - Python: upgrade urllib3 to fixed secure version compatible with stack.
   - Frontend: upgrade vulnerable vite/esbuild/postcss chain and re-test build/runtime.
4. Execute payment and trading E2E validation in production-like HTTPS environment.
5. Record rollback drill evidence and monitoring/alerting checks.
