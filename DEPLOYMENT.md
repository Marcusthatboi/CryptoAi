# Production Deployment

Canonical deployment documentation has moved to `docs/DEPLOYMENT_GUIDE.md`.
This file is kept as a quick summary reference.

## Included infrastructure

- `Dockerfile.backend` for the FastAPI backend
- `frontend/Dockerfile` for the Vite frontend served by Nginx
- `docker-compose.prod.yml` for MongoDB, backend, and frontend
- `.env.example` for required runtime configuration

## Quick start

1. Copy `.env.example` to `.env`
2. Replace all placeholder secrets
3. Build and start the stack:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

4. Open the app at `http://localhost:8080`
5. Backend health endpoint: `http://localhost:8002/health`

## Notes

- Frontend API and WebSocket URLs are now environment-configurable through `VITE_API_BASE_URL` and `VITE_WS_URL`
- Backend runs with `uvicorn --workers 2` for better production concurrency
- MongoDB pool settings are tuned through environment variables for higher throughput
- For multi-instance deployments, replace the in-memory endpoint limiter with a shared store such as Redis
- For internet-facing deployments, place the stack behind TLS termination and restrict the MongoDB port
