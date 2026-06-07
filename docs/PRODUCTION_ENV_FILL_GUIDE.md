# Production Env Fill Guide

Use this guide to finish the final launch blockers reported by `deploy/ops/predeploy_env_check.py`.

## Current Blockers (from latest check)

- `STRIPE_SECRET_KEY` is test key
- `STRIPE_PUBLISHABLE_KEY` is test key
- `VITE_STRIPE_PUBLISHABLE_KEY` is test key
- `STRIPE_WEBHOOK_SECRET` is placeholder

## Backend `.env` Required Production Values

Set these in `.env` (or your deployment secret manager):

```env
APP_ENV=production
ENVIRONMENT=production
FRONTEND_ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
STRIPE_SECRET_KEY=sk_live_REPLACE_ME
STRIPE_PUBLISHABLE_KEY=pk_live_REPLACE_ME
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_ME
```

Notes:
- Use comma-separated origins for `FRONTEND_ALLOWED_ORIGINS`.
- Do not keep live keys committed to source control.

## Frontend `frontend/.env.local` Required Production Values

```env
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_REPLACE_ME
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
```

Notes:
- `VITE_*` values are bundled into frontend assets at build time.
- Rebuild frontend after changing these values.

## Stripe and Apple Pay Launch Validation

1. Stripe dashboard
- Confirm live mode is enabled.
- Confirm Apple Pay domain verification includes your production frontend domain.
- Confirm webhook endpoint points to your production backend and uses the same `whsec_` value in backend env.

2. HTTPS and wallet validation
- Open the production URL over `https://`.
- Validate checkout on Safari with a Wallet-enabled device.
- Verify success, cancel, and failure flows.

## Command Checklist

Run these from repo root after filling values:

```powershell
c:/Users/marcu/CryproAI/.venv/Scripts/python.exe deploy/ops/predeploy_env_check.py
```

Expected output:
- `LAUNCH_READY: YES`

Optional confidence checks:

```powershell
Set-Location frontend
npm run build
Set-Location ..
.\.venv\Scripts\python.exe -m pytest -q tests
```

## Final Gate

Only proceed with release when:
- `LAUNCH_READY: YES`
- Stripe live keys are aligned backend + frontend
- Apple Pay domain verification and Safari Wallet device test are both complete
