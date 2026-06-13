# Deployment Guide

This guide covers local production-like deployment, CI/CD automation, and high-availability deployment patterns.

## 1) Deployment Modes

- Local developer mode: backend + frontend started separately.
- Containerized mode: baseline compose stack (`docker-compose.prod.yml`).
- High-availability compose mode: load-balanced dual backend stack (`docker-compose.ha.yml`).
- Kubernetes mode: multi-replica backend/frontend with HPA (`deploy/k8s/`).

## 2) Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Python 3.11+ for non-container local backend work
- Node.js 18+ for non-container frontend work
- Stripe keys if billing flows are enabled

## 3) Configuration

Copy `.env.example` to `.env` and provide values for:
- `SECRET_KEY`
- `MONGODB_URL`
- `DB_NAME`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- pool and websocket limits as needed

Frontend runtime env vars (container build args or Vite env):
- `VITE_API_BASE_URL`
- `VITE_WS_URL`
- `VITE_STRIPE_PUBLISHABLE_KEY`

## 4) Recommended Local Startup (non-container)

Backend:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
```

Frontend:
```powershell
cd frontend
npm run build
npm run preview:prod
```

Expected URLs:
- API: `http://localhost:8002`
- API docs: `http://localhost:8002/docs`
- Frontend production preview: `http://localhost:5175`

This mode is independent of Visual Studio Code. The frontend runs from the built `dist/` output and does not require the editor to stay open.

For Windows systems that should keep running after VS Code is closed or after reboot, install the included startup tasks:

```powershell
./INSTALL_SERVICES_ADMIN.bat
```

This installer creates three scheduled tasks:
- backend on port `8002`
- frontend production preview on port `5175`
- Cloudflare tunnel process

The tasks run at system startup and are configured to restart automatically if a process exits.

## 5) Docker Compose Production-Like Startup

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

Services:
- MongoDB: `localhost:27017`
- Backend: `localhost:8002`
- Frontend (Nginx): `localhost:8080`

Health checks:
- `GET http://localhost:8002/health`
- open `http://localhost:8080`

Stop stack:
```powershell
docker compose -f docker-compose.prod.yml down
```

## 6) High-Availability Docker Compose Startup

Use the HA compose topology for active-active backend nodes behind an API gateway:

```powershell
docker compose -f docker-compose.ha.yml up --build -d
```

HA topology components:
- `backend_a` and `backend_b` FastAPI instances
- `api_gateway` (Nginx) with upstream load balancing and websocket proxying
- shared MongoDB service

Traffic flow:
1. frontend calls `localhost:8002`
2. `api_gateway` load-balances requests to backend replicas
3. websocket upgrades are proxied through the gateway

Convenience scripts:
- PowerShell: `deploy/scripts/deploy.ps1`
- Bash: `deploy/scripts/deploy.sh`

Script examples:
```powershell
./deploy/scripts/deploy.ps1
```
```bash
./deploy/scripts/deploy.sh
```

## 7) CI/CD Automation

### GitLab CI/CD
Pipeline definition: `.gitlab-ci.yml`

Stages:
1. backend tests
2. frontend build
3. security scans (`pip-audit`, `npm audit`)
4. manual production deployment on `main`

### Jenkins
Pipeline definition: `Jenkinsfile`

Stages:
1. checkout
2. backend tests
3. frontend build
4. security scan gates
5. deploy on `main`

## 8) Kubernetes Deployment (Scalable HA Option)

Kubernetes manifests are provided under `deploy/k8s/`:
- namespace: `deploy/k8s/namespace.yaml`
- database: `deploy/k8s/mongo.yaml`
- backend deployment/service/HPA: `deploy/k8s/backend.yaml`
- frontend deployment/service/ingress: `deploy/k8s/frontend.yaml`
- secret template: `deploy/k8s/secrets.template.yaml`

Apply sequence:
```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/secrets.template.yaml
kubectl apply -f deploy/k8s/mongo.yaml
kubectl apply -f deploy/k8s/backend.yaml
kubectl apply -f deploy/k8s/frontend.yaml
```

Scale behavior:
- backend starts with 3 replicas and autoscaling to 10 based on CPU utilization
- frontend starts with 2 replicas

## 9) Security Hardening Checklist

- Replace all placeholder secrets from `.env.example`.
- Keep backend on `APP_ENV=production` and `ENVIRONMENT=production` for stricter startup checks.
- Restrict CORS origins to known frontend hosts.
- Place frontend/backend behind TLS termination in internet-facing deployments.
- Keep MongoDB non-public or strictly firewall-restricted.
- Configure Stripe webhook endpoint with signing secret validation.
- Rotate credentials regularly.
- Run containers as non-root users where possible.
- Enable `no-new-privileges` and readonly root filesystem for gateway/frontend.
- Keep gateway proxy timeout and body-size limits conservative.

## 10) Scalability Checklist

- Increase uvicorn workers in backend container for CPU-bound throughput.
- Tune Mongo pool settings:
  - `MONGO_MAX_POOL_SIZE`
  - `MONGO_MIN_POOL_SIZE`
- Move in-memory rate limiting to Redis for multi-instance deployments.
- Add centralized logging/metrics (OpenTelemetry, ELK, Grafana stack, etc.).
- Use CDN and static caching for frontend assets.
- Use Kubernetes HPA and proper resource requests/limits for burst traffic.

## 11) Operations Runbook

Common checks:
1. API unavailable (`ERR_CONNECTION_REFUSED`): verify backend process/container is running on port 8002.
2. WebSocket disconnect loop: confirm `/ws` is reachable and backend is healthy.
3. Stripe checkout failures: verify live/test key alignment and webhook secret.
4. Mongo errors: verify DB connectivity and credentials.

Log access:
```powershell
docker compose -f docker-compose.prod.yml logs -f backend
```
```powershell
docker compose -f docker-compose.prod.yml logs -f frontend
```

HA log access:
```powershell
docker compose -f docker-compose.ha.yml logs -f backend_a backend_b api_gateway
```

## 12) Release Procedure (Baseline)

1. Run automated tests in `tests/`.
2. Build frontend (`npm run build`).
3. Validate backend compile (`python -m py_compile`).
4. Run dependency vulnerability scans (`pip-audit`, `npm audit`).
5. Deploy with tagged version and rollback plan.

## 13) Documentation Sync Requirement

Any deployment-affecting change must update:
- this file (`docs/DEPLOYMENT_GUIDE.md`)
- `.env.example`
- `docker-compose.prod.yml` if topology changed
- `docker-compose.ha.yml` and `deploy/k8s/*` if HA topology changed
- CI files (`.gitlab-ci.yml`, `Jenkinsfile`) if pipeline behavior changed

## 14) Post-Deployment Support Operations

Operational scripts:
- health checks: `deploy/ops/healthcheck.ps1`, `deploy/ops/healthcheck.sh`
- maintenance checks: `deploy/ops/maintenance.ps1`, `deploy/ops/maintenance.sh`

Examples:
```powershell
./deploy/ops/healthcheck.ps1
./deploy/ops/maintenance.ps1 -IncludeBuild -SecurityScan
```

See `docs/SUPPORT_MAINTENANCE_GUIDE.md` for ongoing support model, incident process, and maintenance cadence.
