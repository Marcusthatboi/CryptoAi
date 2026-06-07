from datetime import datetime
import os

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }


@router.get("/")
async def root(request: Request):
    """Root endpoint with API information."""
    forwarded_proto = request.headers.get("x-forwarded-proto")
    request_scheme = forwarded_proto.split(",")[0].strip() if forwarded_proto else request.url.scheme
    ws_scheme = "wss" if request_scheme == "https" else "ws"
    host = request.headers.get("host") or request.url.netloc
    websocket_url = f"{ws_scheme}://{host}/ws"

    return {
        "application": "CryptoAI API",
        "version": "1.0.0",
        "description": "Real-time cryptocurrency tracking with AI analysis",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "base_url": f"{request_scheme}://{host}",
        "docs": "/docs",
        "health": "/health",
        "websocket": websocket_url,
        "auth": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "profile": "GET /auth/profile"
        },
        "portfolio": {
            "summary": "GET /api/user/portfolio",
            "invest_fake": "POST /api/user/portfolio/invest/fake",
            "invest_real": "POST /api/user/portfolio/invest/real"
        },
        "realtime": {
            "transport": "websocket",
            "endpoint": "/ws",
            "topics": ["price_update", "portfolio_update", "alert_update"]
        }
    }
