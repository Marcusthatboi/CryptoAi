"""
Email Verification Routes
=========================
Sends a time-limited email verification token on demand and validates it.
Marks the user's account as verified once the token is confirmed.
"""

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.db import get_db
from backend.support_email import send_email

logger = logging.getLogger(__name__)

EMAIL_VERIFY_TOKEN_TTL_MINUTES = int(os.getenv("EMAIL_VERIFY_TOKEN_TTL_MINUTES", "60"))
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://dacryptobeast.com").rstrip("/")
SUPPORT_EMAIL_FROM = os.getenv("SUPPORT_EMAIL_FROM", os.getenv("SUPPORT_EMAIL_TO", "cryptosupport74@gmail.com"))


class VerifyEmailRequest(BaseModel):
    token: str


async def _upsert_verification_token(db, user_id: str) -> str:
    token = secrets.token_urlsafe(48)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=EMAIL_VERIFY_TOKEN_TTL_MINUTES)).isoformat()
    col = db["email_verifications"]
    await col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "token": token, "expires_at": expires_at, "used": False}},
        upsert=True,
    )
    return token


async def _lookup_verification_token(db, token: str) -> Optional[dict]:
    col = db["email_verifications"]
    return await col.find_one({"token": token, "used": False})


async def _mark_token_used(db, token: str):
    col = db["email_verifications"]
    await col.update_one({"token": token}, {"$set": {"used": True}})


async def _mark_user_verified(db, user_id: str):
    col = db["users"]
    from bson import ObjectId
    try:
        oid = ObjectId(user_id)
    except Exception:
        oid = user_id
    await col.update_one(
        {"_id": oid},
        {"$set": {"email_verified": True, "email_verified_at": datetime.now(timezone.utc).isoformat()}},
    )


def create_email_verification_router(get_current_user_dependency, get_db_fn=get_db):
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    @router.post("/send-verification-email")
    async def send_email_verification(
        current_user: str = Depends(get_current_user_dependency),
        db=Depends(get_db_fn),
    ):
        """Send a verification email to the authenticated user's registered email address."""
        from bson import ObjectId
        col = db["users"]
        try:
            oid = ObjectId(current_user)
        except Exception:
            oid = current_user
        user = await col.find_one({"_id": oid})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.get("email_verified"):
            return {"status": "ok", "message": "Email is already verified"}

        email = str(user.get("email") or "").strip()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email address is associated with your account. Add an email in Settings first.",
            )

        token = await _upsert_verification_token(db, current_user)
        verify_link = f"{FRONTEND_BASE_URL}/verify-email?token={token}"
        body = (
            f"Hello {user.get('username', 'there')},\n\n"
            "Please verify your DaCryptoBeast email address by clicking the link below:\n\n"
            f"{verify_link}\n\n"
            f"This link expires in {EMAIL_VERIFY_TOKEN_TTL_MINUTES} minutes.\n\n"
            "If you did not request this, you can safely ignore this email."
        )

        try:
            send_email(
                to_email=email,
                subject="Verify your DaCryptoBeast email",
                body=body,
                reply_to=SUPPORT_EMAIL_FROM,
            )
        except RuntimeError as exc:
            logger.warning("Email verification send failed (SMTP not configured): %s", exc)
            return {
                "status": "degraded",
                "message": "Email sending is not configured on this server. Contact support to verify your account.",
                "verify_link_debug": verify_link if os.getenv("APP_ENV", "development") != "production" else None,
            }

        return {"status": "ok", "message": f"Verification email sent to {email}"}

    @router.post("/verify-email")
    async def verify_email(payload: VerifyEmailRequest, db=Depends(get_db_fn)):
        """Confirm email ownership using the token from the verification email."""
        record = await _lookup_verification_token(db, payload.token)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        expires_at_str = str(record.get("expires_at") or "")
        if expires_at_str:
            try:
                expires_dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                if expires_dt.tzinfo is None:
                    expires_dt = expires_dt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires_dt:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verification link has expired. Request a new one.",
                    )
            except (ValueError, TypeError):
                pass

        user_id = str(record.get("user_id", ""))
        await _mark_token_used(db, payload.token)
        await _mark_user_verified(db, user_id)

        return {"status": "ok", "message": "Email verified successfully! Your account is now verified."}

    @router.get("/verification-status")
    async def get_verification_status(
        current_user: str = Depends(get_current_user_dependency),
        db=Depends(get_db_fn),
    ):
        """Return current email verification status for the authenticated user."""
        from bson import ObjectId
        col = db["users"]
        try:
            oid = ObjectId(current_user)
        except Exception:
            oid = current_user
        user = await col.find_one({"_id": oid})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "email_verified": bool(user.get("email_verified")),
            "email": str(user.get("email") or ""),
            "email_verified_at": user.get("email_verified_at"),
        }

    return router
