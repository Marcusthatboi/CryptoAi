# CryptoAI Full-Stack Onboarding

This document is for new contributors joining the GitHub repo and working on both the frontend and backend.

## What You Need Installed

Install these tools before working on the project:

1. Git
2. Python 3.12+ with `venv`
3. Node.js 18+ or 20 LTS
4. npm (bundled with Node.js)
5. Docker Desktop if you want to run the full stack with containers locally or deploy the VPS stack
6. PowerShell 7+ on Windows is recommended
7. Cloudflare access if you are working on the public tunnel or DNS/rules

You do not need a separate local MongoDB install for the normal production-style stack because the Docker compose setup includes MongoDB.

## Repository Layout

- `backend/` - FastAPI API, auth, subscriptions, WebSocket manager, trading and support routes
- `frontend/` - React + Vite dashboard
- `src/` - shared market/tracker utilities used by backend code
- `tests/` - automated backend tests
- `deploy/vps/` - production compose stack, Caddy config, and VPS deployment files

## Frontend Commands

From the repo root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev server:
- Local URL usually: `http://localhost:5173/`

Useful frontend commands:

```powershell
cd frontend
npm run build
npm run preview
npm run preview:prod
```

## Backend Commands

From the repo root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 --reload
```

Backend local URL:
- `http://localhost:8002`

Useful backend checks:

```powershell
python -m py_compile backend/main.py
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

## Local Full-Stack Startup

Open two terminals.

Terminal 1 - backend:

```powershell
cd c:\Users\marcu\CryproAI
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002 --reload
```

Terminal 2 - frontend:

```powershell
cd c:\Users\marcu\CryproAI\frontend
npm install
npm run dev
```

Frontend talks to the backend on port `8002`.

## Windows Launcher Scripts

If you want the repo-provided wrappers, use these:

- `start_backend.bat` - starts the backend only
- `start_frontend.bat` - starts the frontend preview only
- `start_production.bat` - starts backend, tunnel, and production frontend preview

On macOS/Linux, the equivalents are:

- `start_backend.sh`
- `start_frontend.sh`

## Production / Public Startup

### Local Production-Like Preview on Windows

This starts the backend, Cloudflare tunnel, and production frontend preview in separate windows:

```powershell
start_production.bat
```

Expected access points:
- Frontend local preview: `http://127.0.0.1:5175`
- Frontend public: `https://dacryptobeast.com`
- API public: `https://api.dacryptobeast.com`
- Health check: `https://api.dacryptobeast.com/health`

### VPS / Docker Compose Production Stack

Production on the VPS is managed from `deploy/vps/` with Docker Compose and Caddy.

```powershell
cd deploy/vps
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d --build
```

To restart just the main services after code changes:

```powershell
cd deploy/vps
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d --build backend frontend
docker compose --env-file .env.vps -f docker-compose.vps.yml restart caddy
```

## Public URLs

- Frontend: `https://dacryptobeast.com`
- Frontend WWW: `https://www.dacryptobeast.com`
- Backend API: `https://api.dacryptobeast.com`
- Backend health: `https://api.dacryptobeast.com/health`

## Required Environment Files

You will usually need:

- `.env` for local development
- `deploy/vps/.env.vps` for production deployment

Important backend settings include:

- `MONGODB_URL`
- `DB_NAME`
- `SECRET_KEY`
- `FRONTEND_ALLOWED_ORIGINS`
- `APP_ENV`

## Common Validation Commands

```powershell
python -m py_compile backend/main.py
cd frontend
npm run build
```

If you want to verify the public stack:

```powershell
curl.exe -i https://api.dacryptobeast.com/health
curl.exe -I https://dacryptobeast.com/sw.js
```

## Notes for New Contributors

1. Keep backend changes in `backend/` and add tests where possible.
2. Keep frontend changes in `frontend/` and run a production build before merging.
3. Use the backend on port `8002` for local development.
4. Avoid hardcoding hosts; use the repo’s configured environment variables and deployment settings.
5. If you touch CORS, cache, or service worker behavior, verify the public domain after deployment.

## Recommended First Checks After Cloning

1. Install dependencies.
2. Start the backend on port `8002`.
3. Start the frontend on `5173`.
4. Confirm `http://localhost:8002/health` works.
5. Confirm the frontend can call the API without CORS errors.
