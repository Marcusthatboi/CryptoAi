# Release Schedule

## Schedule Overview

This schedule provides a rolling release plan for stakeholders.

## 2026-06 (Current Cycle)

### Release Window: Week of 2026-06-03

Scope:
- Production-readiness package deployment
- Admin/customer management rollout
- CI/CD pipeline activation
- Documentation and support framework release

Entry Criteria:
- Automated backend tests pass
- Frontend build passes
- Security scan findings triaged and accepted with mitigation plan
- Deployment runbook validated

Exit Criteria:
- Services healthy after rollout
- No Sev-1/Sev-2 incidents in first 24 hours
- Stakeholder release notes distributed

## 2026-06 Mid-Cycle Patch Window

### Target: Week of 2026-06-10

Scope:
- Dependency vulnerability remediation
- Image refresh and lockfile updates
- Potential hotfixes from production telemetry

## 2026-06 Late-Cycle Improvement Window

### Target: Week of 2026-06-17

Scope:
- Observability stack expansion (dashboards and alert rules)
- Frontend bundle optimization
- Horizontal rate-limiter design (Redis-backed)

## Release Communication Milestones

Per release:
1. T-3 days: publish release candidate scope to PM + dev stakeholders.
2. T-1 day: publish deployment plan and maintenance window notice.
3. T day: publish release notes and status update.
4. T+1 day: publish post-release health summary.

## Change Control and Approvals

Required approvals before production release:
- Engineering lead approval (technical readiness)
- Product/project manager approval (scope/timing)
- Operations approval (deployment window and rollback readiness)

## Rollback Schedule Policy

- If Sev-1 impact occurs during release window, rollback decision target is within 15 minutes.
- If Sev-2 impact persists beyond 60 minutes, rollback or feature gate is required.

## Update Cadence

- This schedule is reviewed weekly and updated after each release.
