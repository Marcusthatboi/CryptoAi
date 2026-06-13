"""
Exchange Key Registration Routes
=================================
Allows authenticated users to register their exchange API public keys on the server.
Only the public (read-only) key is stored — never the secret.
Keys are validated as non-empty and stored per exchange per user.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

from backend.db import get_db

logger = logging.getLogger(__name__)

SUPPORTED_EXCHANGES = {"binance", "binance_us", "alpaca", "coinbase", "kraken", "bybit"}


class RegisterPublicKeyRequest(BaseModel):
    exchange: str
    public_key: str
    label: Optional[str] = None  # optional human-readable label, e.g. "main trading key"


class DeletePublicKeyRequest(BaseModel):
    exchange: str


def create_exchange_key_router(get_current_user_dependency, get_db_fn=get_db):
    router = APIRouter(prefix="/api/user/exchange-keys", tags=["exchange-keys"])

    @router.post("/register")
    async def register_exchange_public_key(
        payload: RegisterPublicKeyRequest,
        current_user: str = Depends(get_current_user_dependency),
        db=Depends(get_db_fn),
    ):
        """
        Register an exchange API public (non-secret) key for the authenticated user.
        Only the public key is stored. Never submit your secret key.
        """
        exchange = str(payload.exchange or "").strip().lower()
        public_key = str(payload.public_key or "").strip()

        if exchange not in SUPPORTED_EXCHANGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported exchange '{exchange}'. Supported: {sorted(SUPPORTED_EXCHANGES)}",
            )

        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="public_key must not be empty",
            )

        if len(public_key) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="public_key appears too short to be valid",
            )

        if len(public_key) > 512:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="public_key exceeds maximum allowed length",
            )

        col = db["user_exchange_keys"]
        now = datetime.now(timezone.utc).isoformat()
        await col.update_one(
            {"user_id": current_user, "exchange": exchange},
            {
                "$set": {
                    "user_id": current_user,
                    "exchange": exchange,
                    "public_key": public_key,
                    "label": str(payload.label or "").strip() or None,
                    "registered_at": now,
                    "updated_at": now,
                }
            },
            upsert=True,
        )

        logger.info("Exchange public key registered: user=%s exchange=%s", current_user, exchange)

        return {
            "status": "ok",
            "message": f"Public key for {exchange} registered successfully",
            "exchange": exchange,
            "registered_at": now,
        }

    @router.get("/")
    async def list_registered_exchange_keys(
        current_user: str = Depends(get_current_user_dependency),
        db=Depends(get_db_fn),
    ):
        """List all exchanges for which the user has a registered public key."""
        col = db["user_exchange_keys"]
        records = await col.find(
            {"user_id": current_user},
            {"_id": 0, "user_id": 0},
        ).to_list(length=50)

        # Mask the key for display (show first 6 + last 4 chars)
        def mask_key(key: str) -> str:
            if len(key) <= 10:
                return "***"
            return f"{key[:6]}...{key[-4:]}"

        masked = [
            {
                "exchange": r.get("exchange"),
                "public_key_masked": mask_key(str(r.get("public_key", ""))),
                "label": r.get("label"),
                "registered_at": r.get("registered_at"),
                "updated_at": r.get("updated_at"),
            }
            for r in records
        ]

        return {
            "status": "ok",
            "registered_exchanges": [r["exchange"] for r in masked],
            "keys": masked,
        }

    @router.delete("/")
    async def delete_exchange_public_key(
        payload: DeletePublicKeyRequest,
        current_user: str = Depends(get_current_user_dependency),
        db=Depends(get_db_fn),
    ):
        """Remove a registered exchange public key for the authenticated user."""
        exchange = str(payload.exchange or "").strip().lower()
        col = db["user_exchange_keys"]
        result = await col.delete_one({"user_id": current_user, "exchange": exchange})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No registered key found for exchange '{exchange}'",
            )

        return {"status": "ok", "message": f"Public key for {exchange} removed"}

    return router
