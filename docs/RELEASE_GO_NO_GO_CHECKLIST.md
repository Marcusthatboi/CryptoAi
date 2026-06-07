# Release Go/No-Go Checklist

Use this checklist during final release review. Mark each gate as PASS or FAIL and stop release on any FAIL in Critical gates.

## Release Metadata

- Release version/tag: pending final tag
- Environment: production
- Release owner: pending assignment
- Date/time (UTC): 2026-06-02T19:18:30Z
- Change window: pending final approval window

## Gate 1 - Critical Security and Config

- [ ] PASS / [x] FAIL: No placeholder secrets in backend env (`SECRET_KEY`, Stripe keys, provider keys).
- [x] PASS / [ ] FAIL: Frontend uses production API/WS URLs (`VITE_API_BASE_URL`, `VITE_WS_URL`).
- [x] PASS / [ ] FAIL: CORS restricted to known origins only.
- [ ] PASS / [x] FAIL: Stripe webhook secret configured and signature validation enabled.
- [x] PASS / [ ] FAIL: Production runs with strict env mode (`APP_ENV=production`, `ENVIRONMENT=production`).

Blocking note if FAIL:
- `deploy/ops/predeploy_env_check.py` now reports 4 blockers.
- Remaining blockers are Stripe live key alignment and webhook secret configuration.

## Gate 2 - Payments and Apple Pay Readiness

- [ ] PASS / [x] FAIL: Stripe live/test mode alignment verified across backend and frontend keys.
- [ ] PASS / [x] FAIL: Upgrade checkout success path verified.
- [ ] PASS / [x] FAIL: Upgrade checkout failure/cancel path verified.
- [ ] PASS / [x] FAIL: Apple Pay domain verification completed in Stripe for deployed domain.
- [ ] PASS / [x] FAIL: Apple Pay tested on Safari + Wallet device over HTTPS.

Blocking note if FAIL:
- Active env still uses `sk_test_`/`pk_test_` keys.
- No production Stripe dashboard/domain verification evidence captured in this workspace audit.

## Gate 3 - Trading Safety

- [ ] PASS / [x] FAIL: Real trade precheck endpoint returns ready for intended provider(s).
- [ ] PASS / [x] FAIL: Small-value real trade test completed successfully.
- [ ] PASS / [x] FAIL: Payment success + trade failure path tested (refund/compensation flow).
- [ ] PASS / [x] FAIL: Execution provider readiness states are visible and accurate.

Blocking note if FAIL:
- No fresh production-like trading E2E validation evidence was executed in this final pass.

## Gate 4 - Portfolio and Data Integrity

- [ ] PASS / [x] FAIL: Holdings + sold-position profit/loss appears accurate.
- [ ] PASS / [x] FAIL: Fake and real account totals remain separated and correct.
- [ ] PASS / [x] FAIL: Buying power add flow persists and reflects correctly after refresh.
- [ ] PASS / [x] FAIL: No data-loss regression in recent activity/transactions.

Blocking note if FAIL:
- Portfolio/data integrity checks were not re-executed against production-like runtime in this final pass.

## Gate 5 - Runtime Reliability

- [ ] PASS / [x] FAIL: Backend health endpoint responds in production.
- [ ] PASS / [x] FAIL: Frontend loads without console errors on initial route.
- [ ] PASS / [x] FAIL: Websocket/realtime features connect and recover after reconnect.
- [ ] PASS / [x] FAIL: Logs and alerts configured for 5xx, webhook failures, and trade execution errors.

Blocking note if FAIL:
- Production deployment/runtime validation was not executed in this workspace session.
- No deployment-target monitoring/alerting verification evidence captured.

## Gate 6 - Build and Test Evidence

- [x] PASS / [ ] FAIL: Frontend production build passed.
- [x] PASS / [ ] FAIL: Backend tests passed.
- [x] PASS / [ ] FAIL: Security scan gates reviewed (`pip-audit`, `npm audit`).
- [ ] PASS / [x] FAIL: Rollback plan documented and validated.

Evidence links/notes:
- Frontend build PASS: `npm run build` on 2026-06-02.
- Backend tests PASS: `pytest -q tests` (19 passed) from rerun audit evidence.
- Security scans PASS: `npm audit` clean and `pip_audit` no known vulnerabilities from rerun audit evidence.
- Rollback policy documented in `docs/RELEASE_SCHEDULE.md`, but no validation drill evidence recorded.

## 15-Minute Cutover Runbook

1. Confirm all Critical gates are PASS.
2. Tag release and store artifact references.
3. Deploy backend and verify health.
4. Deploy frontend and verify route load + API connectivity.
5. Execute smoke checks:
- Login
- Subscription upgrade checkout
- Real trade precheck
- Add buying power
- Portfolio page load and P/L cards
6. Monitor logs/metrics for 15 minutes.
7. If critical error rate rises or payments/trades fail, roll back immediately.

## Final Decision

- [ ] GO
- [x] NO-GO

Approvers:
- Engineering: pending
- Product: pending
- Operations: pending
