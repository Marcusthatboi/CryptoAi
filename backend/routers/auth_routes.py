import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserProfile,
    UpdateAccountSettings,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    create_access_token,
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    set_user_password_reset_token,
    reset_user_password_with_token,
    decrypt_account_settings,
    update_user_account_settings,
)
from backend.db import get_db
from backend.support_email import send_support_email, send_email


def create_auth_router(
    get_current_user_dependency,
    user_is_admin_fn,
    logger,
    get_db_fn=get_db,
    create_user_fn=create_user,
    authenticate_user_fn=authenticate_user,
    get_user_by_username_fn=get_user_by_username,
    get_user_by_email_fn=get_user_by_email,
    get_user_by_id_fn=get_user_by_id,
    set_user_password_reset_token_fn=set_user_password_reset_token,
    reset_user_password_with_token_fn=reset_user_password_with_token,
):
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register", response_model=TokenResponse)
    async def register_user(user_data: UserRegister):
        try:
            db = await get_db_fn()
            user_doc = await create_user_fn(db, user_data.username, user_data.password, user_data.email)
            user_id = str(user_doc["_id"])

            token_data = {"sub": user_data.username, "user_id": user_id}
            access_token = create_access_token(token_data)

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                username=user_data.username,
                user_id=user_id,
                is_admin=user_is_admin_fn(user_doc),
                role=user_doc.get("role") or ("admin" if user_is_admin_fn(user_doc) else "user"),
                expires_in=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) * 60,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Registration error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(exc)}",
            )

    @router.post("/login", response_model=TokenResponse)
    async def login_user(user_data: UserLogin):
        try:
            db = await get_db_fn()
            user = await authenticate_user_fn(db, user_data.username, user_data.password)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                )

            user_id = str(user["_id"])
            token_data = {"sub": user_data.username, "user_id": user_id}
            access_token = create_access_token(token_data)

            logger.info(f"✅ User logged in: {user_data.username}")

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                username=user_data.username,
                user_id=user_id,
                is_admin=user_is_admin_fn(user),
                role=user.get("role") or ("admin" if user_is_admin_fn(user) else "user"),
                expires_in=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) * 60,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Login error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(exc)}",
            )

    @router.get("/profile", response_model=UserProfile)
    async def get_user_profile(current_user: str = Depends(get_current_user_dependency)):
        try:
            db = await get_db_fn()
            user = await get_user_by_id_fn(db, current_user)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            return UserProfile(
                user_id=str(user["_id"]),
                username=user["username"],
                email=user.get("email"),
                is_admin=user_is_admin_fn(user),
                role=user.get("role") or ("admin" if user_is_admin_fn(user) else "user"),
                created_at=user["created_at"],
                updated_at=user["updated_at"],
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching profile: {str(exc)}",
            )

    @router.post("/forgot-password")
    async def forgot_password(payload: ForgotPasswordRequest):
        """Create a secure reset token and email a reset link when account exists."""
        try:
            db = await get_db_fn()
            username = str(payload.username or "").strip()
            email = str(payload.email or "").strip()
            frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3001").rstrip("/")

            user = None
            if username:
                user = await get_user_by_username_fn(db, username)
            if not user and email:
                user = await get_user_by_email_fn(db, email)

            # Always return a generic response to avoid account enumeration.
            if user:
                user_email = str(user.get("email") or email or "unknown")
                user_name = str(user.get("username") or username or "unknown")

                reset_token_payload = await set_user_password_reset_token_fn(db, str(user.get("_id")))
                reset_token = reset_token_payload.get("token")
                expires_at = reset_token_payload.get("expires_at")
                reset_link = f"{frontend_base_url}/reset-password?token={reset_token}"

                email_body = (
                    f"Hello {user_name},\n\n"
                    "We received a request to reset your DaCryptoBeast password.\n"
                    "Use the secure link below to set a new password:\n\n"
                    f"{reset_link}\n\n"
                    f"This link expires at {expires_at} UTC.\n"
                    "If you did not request this reset, you can safely ignore this email.\n"
                )

                try:
                    send_email(
                        to_email=user_email,
                        subject="DaCryptoBeast Password Reset",
                        body=email_body,
                        reply_to=os.getenv("SUPPORT_EMAIL_TO", "cryptosupport74@gmail.com")
                    )
                except Exception as send_exc:
                    logger.warning(f"Forgot password reset email failed: {send_exc}")
                    support_payload = {
                        "subject": "DaCryptoBeast Password Reset Fallback",
                        "category": "password_reset",
                        "username": user_name,
                        "user_id": str(user.get("_id", "unknown")),
                        "email": user_email,
                        "summary": "Primary reset email failed; manual assistance required.",
                        "details": (
                            f"Password reset requested at {datetime.utcnow().isoformat()}Z. "
                            f"Submitted username={username or '(none)'}, email={email or '(none)'}"
                        ),
                        "diagnostics": f"Route: POST /auth/forgot-password | reset_link={reset_link}"
                    }
                    try:
                        send_support_email(support_payload)
                    except Exception as email_exc:
                        logger.warning(f"Forgot password support fallback failed: {email_exc}")

            return {
                "ok": True,
                "message": "If the account exists, a password reset request has been submitted."
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Forgot password request failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process forgot password request"
            )

    @router.post("/reset-password")
    async def reset_password(payload: ResetPasswordRequest):
        """Reset account password using a valid reset token."""
        try:
            db = await get_db_fn()
            did_reset = await reset_user_password_with_token_fn(db, payload.token, payload.new_password)
            if not did_reset:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )

            return {
                "ok": True,
                "message": "Password has been reset successfully"
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Reset password failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to reset password"
            )

    @router.post("/update-settings", response_model=UserProfile)
    async def update_account_settings(
        encrypted_payload: UpdateAccountSettings,
        current_user: str = Depends(get_current_user_dependency)
    ):
        """
        Update user account settings (email and/or password) with encrypted payload.
        
        Expects encrypted data with:
        - encryptedData: AES-GCM-256 encrypted JSON with 'email' and/or 'password' fields
        - iv: Initialization vector
        - key: Encryption key
        - algorithm: "AES-GCM-256"
        """
        try:
            # Decrypt the settings data
            decrypted_settings = decrypt_account_settings(encrypted_payload.dict())
            
            email = decrypted_settings.get("email", "").strip()
            password = decrypted_settings.get("password", "").strip()
            
            # Validate that at least one field is provided
            if not email and not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one field (email or password) must be provided"
                )
            
            # Validate email format if provided
            if email and ("@" not in email or "." not in email.split("@")[-1]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format"
                )
            
            # Validate password length if provided
            if password and len(password) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password must be at least 6 characters"
                )
            
            # Update user account settings
            db = await get_db_fn()
            updated_profile = await update_user_account_settings(
                db,
                current_user,
                email=email if email else None,
                password=password if password else None
            )
            
            logger.info(f"✅ Account settings updated for user: {current_user}")
            
            return updated_profile
            
        except HTTPException:
            raise
        except ValueError as ve:
            logger.error(f"Decryption error: {ve}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decrypt settings: {str(ve)}"
            )
        except Exception as exc:
            logger.error(f"Update account settings error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update account settings: {str(exc)}"
            )

    return router
