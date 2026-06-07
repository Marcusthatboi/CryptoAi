# Support and Maintenance Guide

This guide defines operational support, maintenance cadence, and incident handling for CryptoAI.

## 1) Operational Support Model

Support channels:
- engineering on-call (primary)
- product feedback intake (secondary)

Recommended response targets:
- Sev-1 (outage/security breach): acknowledge within 15 minutes
- Sev-2 (major feature degradation): acknowledge within 1 hour
- Sev-3 (minor bug/UI issue): acknowledge within 1 business day

## 2) Monitoring Checklist

Track continuously:
- API availability (`/health`)
- frontend availability
- websocket stability (`/ws` reconnect/error rates)
- API error rates (4xx/5xx)
- latency percentiles for core endpoints
- quota/rate-limit pressure metrics

Run ad-hoc checks:
```powershell
./deploy/ops/healthcheck.ps1
```
```bash
./deploy/ops/healthcheck.sh
```

## 3) Maintenance Cadence

Daily:
- review error logs and alert trends
- check deployment health and key customer flows

Weekly:
- run maintenance suite with build and security scans
- review customer-reported issues and support backlog

Monthly:
- dependency upgrade cycle
- security review and secret rotation validation
- performance regression review

Maintenance commands:
```powershell
./deploy/ops/maintenance.ps1 -IncludeBuild -SecurityScan
```
```bash
./deploy/ops/maintenance.sh --include-build --security-scan
```

Portfolio cost-basis repair (one-time / as-needed):
```powershell
python ./deploy/scripts/repair_portfolio_holdings.py
python ./deploy/scripts/repair_portfolio_holdings.py --apply
```
```bash
python ./deploy/scripts/repair_portfolio_holdings.py
python ./deploy/scripts/repair_portfolio_holdings.py --apply
```

## 4) Incident Response Workflow

1. Triage severity and scope.
2. Mitigate user impact (rollback, scaling, feature flag, traffic shaping).
3. Resolve root cause.
4. Publish incident summary with impact/timeline/actions.
5. Add regression test and runbook update.

## 5) Security Maintenance

- Keep base images and dependencies patched.
- Run `pip_audit` and `npm audit` before production releases.
- Rotate credentials after incidents or exposure risk.
- Keep secrets out of source control and CI logs.
- Review auth/admin controls after major feature releases.

## 6) Performance and UX Improvement Loop

Inputs:
- latency/error dashboards
- support tickets
- user feedback from product channels
- quota pressure analytics from admin dashboard

Process:
1. classify by impact and effort
2. prioritize weekly roadmap
3. release incremental fixes
4. measure post-release metrics

## 7) Release Support Checklist

Pre-release:
- tests passing
- build passing
- security scan reviewed
- migration/deployment plan ready

Post-release:
- run healthcheck scripts
- validate login, dashboard load, pricing checkout, admin access
- monitor logs for elevated errors in first 30-60 minutes

## 8) Ownership and Documentation Hygiene

- Keep this guide in sync with deployment and CI/CD docs.
- Any bugfix touching reliability/security must update tests and docs.
- Every Sev-1/Sev-2 incident should produce a permanent runbook update.
