"""
Encrypted Wallet Module for CryptoAI
Handles encrypted crypto wallet storage and transfers
"""
import base64
import json
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EncryptedWalletAddress(BaseModel):
    """Encrypted wallet address"""
    crypto_symbol: str  # BTC, ETH, USDT, etc.
    encrypted_address: str  # base64 encrypted address
    iv: str  # base64 initialization vector
    label: Optional[str] = None  # User-defined label
    is_default: bool = False

class EncryptedWallet(BaseModel):
    """User's encrypted wallet storage"""
    user_id: str
    wallets: List[EncryptedWalletAddress]
    default_crypto: str = "BTC"
    created_at: str
    updated_at: str

class EncryptedWalletManager:
    """Manages encrypted wallet operations"""
    
    def __init__(self, db=None):
        self.db = db
        self.collection_name = "encrypted_wallets"
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
    
    def generate_salt(self) -> bytes:
        """Generate random salt for key derivation"""
        return os.urandom(16)
    
    def encrypt_wallet_address(self, address: str, user_key: str) -> Dict[str, str]:
        """
        Encrypt a crypto wallet address
        
        Args:
            address: Plain text wallet address
            user_key: User's encryption key/password
            
        Returns:
            Dict with encryptedData, iv, and salt (all base64)
        """
        salt = self.generate_salt()
        key = self.derive_key(user_key, salt)
        
        cipher = AESGCM(key)
        iv = os.urandom(12)  # 96-bit IV for GCM
        
        encrypted_data = cipher.encrypt(
            iv,
            address.encode('utf-8'),
            None
        )
        
        return {
            "encryptedData": base64.b64encode(encrypted_data).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8')
        }
    
    def decrypt_wallet_address(self, encrypted_payload: Dict[str, str], user_key: str) -> str:
        """
        Decrypt a crypto wallet address
        
        Args:
            encrypted_payload: Dict with encryptedData, iv, salt
            user_key: User's encryption key/password
            
        Returns:
            Decrypted wallet address
        """
        encrypted_data = base64.b64decode(encrypted_payload["encryptedData"])
        iv = base64.b64decode(encrypted_payload["iv"])
        salt = base64.b64decode(encrypted_payload["salt"])
        
        key = self.derive_key(user_key, salt)
        
        cipher = AESGCM(key)
        decrypted_data = cipher.decrypt(iv, encrypted_data, None)
        
        return decrypted_data.decode('utf-8')
    
    async def store_wallet(self, user_id: str, wallets: List[EncryptedWalletAddress], default_crypto: str = "BTC") -> bool:
        """Store encrypted wallets in database"""
        if not self.db:
            logger.warning("No database connection, wallet not persisted")
            return False
        
        try:
            collection = self.db[self.collection_name]
            now = datetime.utcnow().isoformat()
            
            wallet_doc = {
                "user_id": user_id,
                "wallets": [w.model_dump() for w in wallets],
                "default_crypto": default_crypto,
                "created_at": now,
                "updated_at": now
            }
            
            await collection.update_one(
                {"user_id": user_id},
                {"$set": wallet_doc},
                upsert=True
            )
            
            logger.info(f"Stored encrypted wallets for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing wallets: {e}")
            return False
    
    async def get_wallets(self, user_id: str) -> Optional[List[EncryptedWalletAddress]]:
        """Retrieve encrypted wallets from database"""
        if not self.db:
            return None
        
        try:
            collection = self.db[self.collection_name]
            doc = await collection.find_one({"user_id": user_id})
            
            if doc and doc.get("wallets"):
                return [EncryptedWalletAddress(**w) for w in doc["wallets"]]
            
            return []
        
        except Exception as e:
            logger.error(f"Error retrieving wallets: {e}")
            return None
    
    async def get_default_wallet(self, user_id: str) -> Optional[EncryptedWalletAddress]:
        """Get user's default wallet"""
        wallets = await self.get_wallets(user_id)
        
        if not wallets:
            return None
        
        for wallet in wallets:
            if wallet.is_default:
                return wallet
        
        return wallets[0] if wallets else None
    
    def validate_crypto_address(self, symbol: str, address: str) -> bool:
        """Validate crypto address format"""
        if not address or len(address) < 10:
            return False
        
        # Symbol-specific validation
        if symbol == "BTC":
            # Legacy (1/3) or SegWit (bc1) addresses
            return address.startswith(("1", "3", "bc1")) and 26 <= len(address) <= 62
        
        elif symbol == "ETH":
            # Ethereum addresses start with 0x and are 42 chars
            return address.startswith("0x") and len(address) == 42
        
        elif symbol == "USDT":
            # ERC-20 or TRC-20
            if address.startswith("0x"):
                return len(address) == 42
            elif address.startswith("T"):
                return len(address) == 34
        
        elif symbol == "SOL":
            # Solana addresses are base58, typically 32-44 chars
            return len(address) >= 32
        
        return True
    
    def mask_address(self, address: str) -> str:
        """Mask wallet address for display"""
        if len(address) <= 8:
            return address[:4] + "..." + address[-4:]
        return address[:6] + "..." + address[-4:]


# Standalone functions for use without database
def encrypt_address(address: str, master_key: str) -> Dict[str, str]:
    """Encrypt a wallet address with master key"""
    manager = EncryptedWalletManager()
    return manager.encrypt_wallet_address(address, master_key)

def decrypt_address(encrypted: Dict[str, str], master_key: str) -> str:
    """Decrypt a wallet address with master key"""
    manager = EncryptedWalletManager()
    return manager.decrypt_wallet_address(encrypted, master_key)
