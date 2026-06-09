"""
Authentication module for CryptoAI
Handles user registration, login, and JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
import hashlib
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, validator, model_validator
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "dacryptobeast_admin").strip().lower()
ALLOW_LEGACY_ADMIN_USERNAME = os.getenv("ALLOW_LEGACY_ADMIN_USERNAME", "false").strip().lower() in {"1", "true", "yes", "on"}


def is_admin_username(username: str) -> bool:
    """Return True when username matches configured admin account identity."""
    normalized = str(username or "").strip().lower()
    if not normalized:
        return False
    if normalized == ADMIN_USERNAME:
        return True
    if ALLOW_LEGACY_ADMIN_USERNAME and normalized == "admin":
        return True
    return False


def has_insecure_secret_key() -> bool:
    """Return True when JWT signing is using the unsafe development default."""
    return not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production"


def has_weak_secret_key() -> bool:
    """Return True when JWT signing key is too short or clearly placeholder-like."""
    value = str(SECRET_KEY or "").strip()
    if not value:
        return True
    if len(value) < 32:
        return True
    lowered = value.lower()
    return any(token in lowered for token in ["replace", "changeme", "todo", "secret-key"])

# Password hashing - use pbkdf2_sha256 which doesn't require external C libraries
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ============================================================================
# Pydantic Models
# ============================================================================

class UserRegister(BaseModel):
    """User registration request model"""
    username: str
    password: str
    email: Optional[str] = None
    
    @validator('username')
    def username_validator(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v
    
    @validator('password')
    def password_validator(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    """User login request model"""
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""
    username: Optional[str] = None
    email: Optional[str] = None

    @validator('email')
    def validate_email_if_present(cls, v):
        value = str(v or '').strip()
        if not value:
            return None
        if '@' not in value or '.' not in value.split('@')[-1]:
            raise ValueError('Invalid email format')
        return value

    @model_validator(mode='after')
    def require_identifier(self):
        username = self.username
        email = self.email
        if not str(username or '').strip() and not str(email or '').strip():
            raise ValueError('Provide username or email')
        return self


class ResetPasswordRequest(BaseModel):
    """Reset password request model."""
    token: str
    new_password: str

    @validator('token')
    def token_validator(cls, v):
        if not str(v or '').strip():
            raise ValueError('Reset token is required')
        return v.strip()

    @validator('new_password')
    def password_validator(cls, v):
        if len(v) < 10:
            raise ValueError('Password must be at least 10 characters')
        return v


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    username: str
    user_id: str
    is_admin: bool = False
    role: str = "user"
    expires_in: int


class UserProfile(BaseModel):
    """User profile model"""
    user_id: str
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    role: str = "user"
    created_at: str
    updated_at: str


class UpdateAccountSettings(BaseModel):
    """Encrypted account settings update model"""
    encryptedData: str  # base64-encoded encrypted data
    iv: str  # base64-encoded initialization vector
    key: str  # base64-encoded encryption key
    algorithm: str = "AES-GCM-256"  # encryption algorithm
    
    @validator('algorithm')
    def validate_algorithm(cls, v):
        if v != "AES-GCM-256":
            raise ValueError("Only AES-GCM-256 is supported")
        return v


# ============================================================================
# Password Utilities
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_password_reset_token() -> str:
    """Create a URL-safe reset token."""
    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    """Hash reset token before storage."""
    return hashlib.sha256(str(token).encode('utf-8')).hexdigest()


def decrypt_account_settings(encrypted_payload: Dict[str, str]) -> Dict[str, Any]:
    """
    Decrypt encrypted account settings update.
    
    Args:
        encrypted_payload: Dictionary containing:
            - encryptedData: base64-encoded encrypted data
            - iv: base64-encoded initialization vector
            - key: base64-encoded encryption key
            - algorithm: encryption algorithm used
    
    Returns:
        Dictionary with decrypted settings (email, password, password_confirmation)
    """
    try:
        import base64
        import json
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        # Validate payload
        required_fields = ['encryptedData', 'iv', 'key', 'algorithm']
        if not all(field in encrypted_payload for field in required_fields):
            raise ValueError("Missing required encryption fields")
        
        algorithm = encrypted_payload['algorithm']
        if algorithm != 'AES-GCM-256':
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Decode inputs
        encrypted_data = base64.b64decode(encrypted_payload['encryptedData'])
        iv = base64.b64decode(encrypted_payload['iv'])
        key = base64.b64decode(encrypted_payload['key'])
        
        # Validate key and IV lengths
        if len(key) != 32:
            raise ValueError("Invalid key length for AES-256")
        if len(iv) != 12:
            raise ValueError("Invalid IV length for GCM")
        
        # Decrypt using AES-GCM
        cipher = AESGCM(key)
        decrypted_data = cipher.decrypt(iv, encrypted_data, None)
        
        # Parse JSON
        settings_data = json.loads(decrypted_data.decode('utf-8'))
        
        return settings_data
    
    except Exception as e:
        logger.error(f"Account settings decryption error: {e}")
        raise ValueError(f"Failed to decrypt account settings: {str(e)}")


# ============================================================================
# JWT Token Utilities
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


# ============================================================================
# User Database Operations
# ============================================================================

async def create_user(db: AsyncIOMotorDatabase, username: str, password: str, email: Optional[str] = None) -> Dict:
    """Create a new user in MongoDB"""
    users_col = db["users"]
    
    # Check if user already exists
    existing_user = await users_col.find_one({"username": username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create user document
    user_doc = {
        "username": username,
        "password": hash_password(password),
        "email": email,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "is_active": True,
        "is_admin": is_admin_username(username),
        "role": "admin" if is_admin_username(username) else "user",
        "portfolio": {
            "total_value": 0,
            "cash": 100000.0,  # Default starting balance
            "holdings": [],
            "personal_buying_power": 0.0,
            "withdrawals": [],
            "activity_log": [],
            "realized_pnl": {
                "overall": 0.0,
                "fake_money": 0.0,
                "real_money": 0.0,
            },
            "last_updated": datetime.utcnow().isoformat()
        },
        "settings": {
            "theme": "dark",
            "notifications": True,
            "default_currency": "USD"
        }
    }
    
    result = await users_col.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    logger.info(f"✅ User created: {username}")
    return user_doc


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> Optional[Dict]:
    """Get user by username"""
    users_col = db["users"]
    user = await users_col.find_one({"username": username})
    return user


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[Dict]:
    """Get user by email (case-insensitive exact match)."""
    users_col = db["users"]
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return None
    user = await users_col.find_one({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
    return user


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    from bson import ObjectId
    users_col = db["users"]
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
        return user
    except:
        return None


async def authenticate_user(db: AsyncIOMotorDatabase, username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password"""
    user = await get_user_by_username(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user["password"]):
        return None
    
    return user


async def set_user_password_reset_token(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, str]:
    """Generate/store a reset token and return raw token + expiration timestamp."""
    from bson import ObjectId

    users_col = db["users"]
    raw_token = create_password_reset_token()
    token_hash = hash_password_reset_token(raw_token)
    expires_at = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    expires_at_iso = expires_at.isoformat()

    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_reset": {
                    "token_hash": token_hash,
                    "expires_at": expires_at_iso,
                    "requested_at": datetime.utcnow().isoformat(),
                },
                "updated_at": datetime.utcnow().isoformat(),
            }
        }
    )

    return {
        "token": raw_token,
        "expires_at": expires_at_iso,
    }


async def reset_user_password_with_token(db: AsyncIOMotorDatabase, token: str, new_password: str) -> bool:
    """Reset user password by token. Returns True on success, False for invalid/expired token."""
    users_col = db["users"]
    token_hash = hash_password_reset_token(token)
    now_iso = datetime.utcnow().isoformat()

    user = await users_col.find_one(
        {
            "password_reset.token_hash": token_hash,
            "password_reset.expires_at": {"$gt": now_iso},
            "is_active": {"$ne": False},
        }
    )

    if not user:
        return False

    await users_col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hash_password(new_password),
                "updated_at": datetime.utcnow().isoformat(),
            },
            "$unset": {
                "password_reset": "",
            },
        }
    )

    return True


async def update_user_portfolio(db: AsyncIOMotorDatabase, user_id: str, portfolio_data: Dict) -> Dict:
    """Update user portfolio data"""
    from bson import ObjectId
    users_col = db["users"]
    
    portfolio_data["last_updated"] = datetime.utcnow().isoformat()
    
    result = await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"portfolio": portfolio_data}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return portfolio_data


async def get_user_portfolio(db: AsyncIOMotorDatabase, user_id: str) -> Dict:
    """Get user portfolio"""
    from bson import ObjectId
    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.get("portfolio", {})


async def update_user_account_settings(db: AsyncIOMotorDatabase, user_id: str, email: Optional[str] = None, password: Optional[str] = None) -> UserProfile:
    """
    Update user account settings (email and/or password).
    
    Args:
        db: AsyncIOMotorDatabase instance
        user_id: User ID to update
        email: New email (optional)
        password: New password (optional)
    
    Returns:
        Updated UserProfile
    """
    from bson import ObjectId
    users_col = db["users"]
    
    # Get current user
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow().isoformat()}
    
    # Update email if provided
    if email:
        # Check if email is already used by another user
        existing_user = await users_col.find_one({
            "email": email,
            "_id": {"$ne": ObjectId(user_id)}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        update_doc["email"] = email
    
    # Update password if provided
    if password:
        if len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        update_doc["password"] = hash_password(password)
    
    # Update user in database
    result = await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Fetch and return updated user profile
    updated_user = await get_user_by_id(db, user_id)
    return UserProfile(
        user_id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user.get("email"),
        is_admin=updated_user.get("is_admin", False),
        role=updated_user.get("role", "user"),
        created_at=updated_user.get("created_at", ""),
        updated_at=updated_user.get("updated_at", "")
    )


async def add_user_holding(db: AsyncIOMotorDatabase, user_id: str, holding: Dict) -> Dict:
    """Add a holding to user portfolio"""
    from bson import ObjectId
    users_col = db["users"]
    
    # Get current portfolio
    user = await get_user_by_id(db, user_id)
    portfolio = user.get("portfolio", {})
    holdings = portfolio.get("holdings", [])
    
    holding_symbol = str(holding.get("symbol", "")).upper()
    holding_type = holding.get("investment_type")

    # Check if holding already exists (keep fake and real holdings separate)
    for h in holdings:
        existing_symbol = str(h.get("symbol", "")).upper()
        existing_type = h.get("investment_type")

        if existing_symbol == holding_symbol and existing_type == holding_type:
            # Update existing holding
            existing_quantity = float(h.get("quantity", 0) or 0)
            incoming_quantity = float(holding.get("quantity", 0) or 0)
            existing_average = float(h.get("average_price", h.get("price", 0)) or 0)
            incoming_price = float(holding.get("price", 0) or 0)

            updated_quantity = existing_quantity + incoming_quantity
            weighted_cost = (existing_quantity * existing_average) + (incoming_quantity * incoming_price)
            updated_average_price = (weighted_cost / updated_quantity) if updated_quantity > 0 else incoming_price

            h["quantity"] = updated_quantity
            h["average_price"] = updated_average_price
            h["price"] = incoming_price if incoming_price > 0 else existing_average
            h["total_value"] = updated_quantity * updated_average_price
            h["updated_at"] = datetime.utcnow().isoformat()
            break
    else:
        # Add new holding
        holding["symbol"] = holding_symbol
        if "average_price" not in holding:
            holding["average_price"] = float(holding.get("price", 0) or 0)
        if "total_value" not in holding:
            holding["total_value"] = float(holding.get("quantity", 0) or 0) * float(holding.get("average_price", 0) or 0)
        holding["created_at"] = datetime.utcnow().isoformat()
        holding["updated_at"] = datetime.utcnow().isoformat()
        holdings.append(holding)
    
    portfolio["holdings"] = holdings
    await update_user_portfolio(db, user_id, portfolio)
    
    return portfolio


async def remove_user_holding(db: AsyncIOMotorDatabase, user_id: str, symbol: str) -> Dict:
    """Remove a holding from user portfolio"""
    from bson import ObjectId
    users_col = db["users"]
    
    # Get current portfolio
    user = await get_user_by_id(db, user_id)
    portfolio = user.get("portfolio", {})
    holdings = portfolio.get("holdings", [])
    
    # Remove holding
    portfolio["holdings"] = [h for h in holdings if h.get("symbol") != symbol]
    await update_user_portfolio(db, user_id, portfolio)
    
    return portfolio
