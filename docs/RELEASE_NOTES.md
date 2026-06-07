# Release Notes

## 2026-06-02 - Production Readiness and Operations Update

### Highlights

- Added admin dashboard and customer management workflows.
- Added endpoint-level rate limiting for expensive AI routes.
- Added shared frontend WebSocket connection model.
- Added Docker HA topology and deployment automation scripts.
- Added Jenkins and GitLab CI/CD pipelines.
- Added Kubernetes deployment manifests (including backend autoscaling).
- Added full documentation hub with API, deployment, admin, user, developer, and support guides.

### New Features

- Admin route and UI for subscription/customer operations.
- Admin APIs:
  - `GET /api/admin/customers`
  - `PATCH /api/admin/customers/{user_id}/subscription`
- Subscription analytics endpoint:
  - `GET /api/subscription/analytics/overview`

### Reliability and Security Improvements

- Rate limiting for:
  - `POST /api/chat`
  - `GET /api/recommendations`
- Improved backend startup guardrails for insecure production config.
- Hardened container images and compose runtime options.
- Health/maintenance scripts for ongoing operations.

### Bug Fixes

- Fixed chat endpoint error handling to preserve HTTP 429 instead of converting it to 500.
- Aligned auth/login payload metadata with admin role flags.
- Corrected backend startup scripts to use port 8002 consistently.

### Deployment and DevOps

- Added:
  - `docker-compose.ha.yml`
  - `deploy/nginx/api-gateway.conf`
  - `deploy/scripts/deploy.ps1`
  - `deploy/scripts/deploy.sh`
  - `Jenkinsfile`
  - `.gitlab-ci.yml`
  - `deploy/k8s/*`

### Documentation

- Added and linked:
  - `docs/API_DOCUMENTATION.md`
  - `docs/DEPLOYMENT_GUIDE.md`
  - `docs/ADMIN_GUIDE.md`
  - `docs/USER_GUIDE.md`
  - `docs/DEVELOPER_GUIDE.md`
  - `docs/SUPPORT_MAINTENANCE_GUIDE.md`
  - `docs/STAKEHOLDER_COMMUNICATION_PLAN.md`

### Known Issues / Follow-ups

- Docker daemon availability/permissions can block local deployment execution.
- Dependency vulnerability findings still require full remediation rollout.
- Frontend bundle-size optimization is pending.
