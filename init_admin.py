"""
Script to initialize default admin user in MongoDB
Run this script once to create the bootstrap admin user.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from passlib.context import CryptContext
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Password hashing defaults to Argon2id while keeping compatibility with legacy hashes.
pwd_context = CryptContext(schemes=["argon2", "pbkdf2_sha256"], deprecated="auto")

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "cryptoai")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "dacryptobeast_admin").strip() or "dacryptobeast_admin"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@dacryptobeast.com").strip() or "admin@dacryptobeast.com"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
FORCE_ADMIN_PASSWORD_ROTATION = os.getenv("FORCE_ADMIN_PASSWORD_ROTATION", "true").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_admin_password() -> tuple[str, bool]:
    """Return configured admin password, generating one when absent."""
    if ADMIN_PASSWORD:
        return ADMIN_PASSWORD, False
    generated = secrets.token_urlsafe(18)
    return generated, True

async def init_admin_user():
    """Create default admin user"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        users_col = db["users"]
        
        # Create unique index on username
        await users_col.create_index([("username", 1)], unique=True)
        
        admin_password, password_generated = _resolve_admin_password()

        # Check if admin already exists
        existing_admin = await users_col.find_one({"username": ADMIN_USERNAME})
        if existing_admin:
            print("✅ Admin user already exists!")
            client.close()
            return
        
        # Create admin user document
        admin_doc = {
            "username": ADMIN_USERNAME,
            "password": pwd_context.hash(admin_password),
            "email": ADMIN_EMAIL,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "is_admin": True,
            "role": "admin",
            "must_change_password": bool(FORCE_ADMIN_PASSWORD_ROTATION),
            "portfolio": {
                "total_value": 100000.0,
                "cash": 100000.0,
                "holdings": [],
                "last_updated": datetime.utcnow().isoformat()
            },
            "settings": {
                "theme": "dark",
                "notifications": True,
                "default_currency": "USD"
            }
        }
        
        result = await users_col.insert_one(admin_doc)
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {ADMIN_USERNAME}")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {admin_password}")
        if password_generated:
            print("   ⚠️ This password was generated automatically because ADMIN_PASSWORD was not set.")
            print("   ⚠️ Save it now and rotate it in production secrets immediately.")
        print(f"   User ID: {result.inserted_id}")
        print(f"\nYou can now login with these credentials at http://localhost:3000/login")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error initializing admin user: {e}")

if __name__ == "__main__":
    print("🔧 Initializing CryptoAI Database...")
    print(f"📍 MongoDB: {MONGO_URL}")
    print(f"🗄️  Database: {DB_NAME}")
    print()
    asyncio.run(init_admin_user())
