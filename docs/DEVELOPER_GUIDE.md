# Developer Guide

This guide is for engineers extending or maintaining the CryptoAI codebase.

## 1) Repository Structure

- `backend/`: FastAPI services, auth, subscriptions, integrations, websocket manager
- `frontend/`: React (Vite) SPA, pages/components/hooks, API client utilities
- `src/`: legacy/utility market tracker logic reused by backend
- `tests/`: backend automated tests (unit/integration/security/load/UAT-smoke)
- `data/`, `plots/`: local data and generated artifacts

## 2) Local Development Setup

### Backend
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 --reload
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Frontend expects backend at port 8002.

## 3) Architecture Summary

Backend:
- FastAPI app in `backend/main.py`
- MongoDB via Motor (`backend/db.py`)
- JWT auth helpers in `backend/auth.py`
- subscription/billing logic in `backend/subscription.py`
- websocket connection management in `backend/websocket_manager.py`

Frontend:
- React Router app shell in `frontend/src/App.jsx`
- auth context in `frontend/src/hooks/useAuth.jsx`
- shared websocket provider in `frontend/src/hooks/useWebSocket.js`
- centralized axios client in `frontend/src/utils/api.js`
- admin page in `frontend/src/pages/AdminDashboardPage.jsx`

## 4) Coding and Extension Guidelines

Backend:
- always re-raise `HTTPException` before broad `except Exception`
- keep endpoint-level rate and quota behavior explicit
- enforce admin-only routes with dependency guards
- add indexes for new high-volume Mongo queries

Frontend:
- use centralized `cryptoAPI` wrapper for HTTP calls
- avoid hardcoded hostnames; use Vite env vars
- keep shared websocket semantics (subscribe/unsubscribe cleanup)
- prefer route guards for protected/admin pages

## 5) Testing Matrix

### Automated backend tests
```powershell
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

### Backend compile check
```powershell
python -m py_compile backend/main.py backend/auth.py
```

### Frontend build check
```powershell
cd frontend
npm run build
```

### Dependency security scans
```powershell
python -m pip_audit
cd frontend
npm audit --omit=dev --json
```

## 6) API Change Workflow

1. Update endpoint implementation.
2. Add or update tests in `tests/`.
3. Update `docs/API_DOCUMENTATION.md`.
4. Validate with test/build/compile commands.
5. Add migration notes for breaking changes.

## 7) Deployment Workflow

Baseline container deployment:
```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

When changing deployment topology:
- update `docker-compose.prod.yml`
- update `.env.example`
- update `docs/DEPLOYMENT_GUIDE.md`

## 8) Common Pitfalls

- Port mismatch between frontend and backend (use 8002 consistently).
- Swallowing HTTPException and returning 500 unexpectedly.
- Forgetting to include admin metadata in auth/profile payloads.
- WebSocket reconnect storms when backend is down.
- Missing cleanup for component-level subscriptions.

## 9) Support Email Delivery Setup

The in-app support form posts to `/api/support/contact` and sends email via SMTP.

Required backend environment variables:
- `SUPPORT_EMAIL_TO=cryptosupport74@gmail.com`
- `SUPPORT_SMTP_HOST=smtp.gmail.com`
- `SUPPORT_SMTP_PORT=587`
- `SUPPORT_SMTP_USERNAME=<smtp username>`
- `SUPPORT_SMTP_PASSWORD=<smtp app password>`
- `SUPPORT_SMTP_USE_TLS=true`
- `SUPPORT_EMAIL_FROM=<optional from address>`

If SMTP credentials are missing, the endpoint returns `500` and the frontend displays an error message.

## 10) Backlog Recommendations

- move in-memory rate limiting to Redis for multi-instance setups
- address datetime UTC deprecation warnings with timezone-aware timestamps
- split large frontend bundle with route-level code splitting
- expand frontend automated test coverage (Vitest + React Testing Library)

## 11) Security Hardening Notes

Backend security defaults now include:
- configurable allowed frontend origins via `FRONTEND_ALLOWED_ORIGINS`
- API docs disabled by default in production unless `ENABLE_API_DOCS=true`
- response hardening headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`)
- `Cache-Control: no-store` on auth, user, support, and integration endpoints
- WebSocket origin validation against allowed frontend origins

Recommended security review routine:
1. Keep `SECRET_KEY` and Stripe credentials out of source control and rotate them regularly.
2. Set explicit production origins in `FRONTEND_ALLOWED_ORIGINS`; do not rely on localhost defaults.
3. Run dependency scans regularly:
	- `python -m pip_audit`
	- `npm audit --omit=dev`
4. Revisit rate limiting before multi-instance deployment; move to Redis or another shared store.
5. Keep API docs disabled in public production environments unless there is a specific operational need.
