"""
Payment encryption/decryption module for handling sensitive credit card data
Uses AES-GCM encryption for symmetric encryption
"""

import base64
import logging
from typing import Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import json

logger = logging.getLogger(__name__)


def derive_key_from_encrypted_key(encrypted_key_base64: str, password: str = None) -> bytes:
    """
    Derive decryption key from the encrypted key sent by client.
    Note: In production, you would use a secure key management service.
    """
    try:
        # Decode the base64 key
        key = base64.b64decode(encrypted_key_base64)
        if len(key) != 32:
            raise ValueError("Invalid key length")
        return key
    except Exception as e:
        logger.error(f"Key derivation error: {e}")
        raise ValueError("Invalid encryption key")


def decrypt_card_data(encrypted_payload: Dict[str, str]) -> Dict[str, str]:
    """
    Decrypt credit card data sent from client.
    
    Args:
        encrypted_payload: Dictionary containing:
            - encryptedData: base64-encoded encrypted data
            - iv: base64-encoded initialization vector
            - key: base64-encoded encryption key
            - algorithm: encryption algorithm used
    
    Returns:
        Dictionary with decrypted card data
    """
    try:
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
        card_data = json.loads(decrypted_data.decode('utf-8'))
        
        return card_data
    
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise ValueError(f"Failed to decrypt payment data: {str(e)}")


def validate_decrypted_card_data(card_data: Dict[str, Any]) -> bool:
    """
    Validate decrypted card data format and values.
    """
    required_fields = ['cardNumber', 'expiryMonth', 'expiryYear', 'cvv', 'cardholderName']
    
    if not all(field in card_data for field in required_fields):
        logger.warning("Missing required card fields")
        return False
    
    # Validate card number length
    if not (13 <= len(str(card_data['cardNumber'])) <= 19):
        logger.warning("Invalid card number length")
        return False
    
    # Validate expiry
    try:
        month = int(card_data['expiryMonth'])
        year = int(card_data['expiryYear'])
        if not (1 <= month <= 12):
            logger.warning("Invalid expiry month")
            return False
        # Basic year validation (2-digit year)
        if year < 0 or year > 99:
            logger.warning("Invalid expiry year")
            return False
    except (ValueError, TypeError):
        logger.warning("Invalid expiry format")
        return False
    
    # Validate CVV
    if not (3 <= len(str(card_data['cvv'])) <= 4):
        logger.warning("Invalid CVV length")
        return False
    
    # Validate cardholder name
    if not isinstance(card_data['cardholderName'], str) or len(card_data['cardholderName']) < 2:
        logger.warning("Invalid cardholder name")
        return False
    
    return True


def mask_card_number(card_number: str) -> str:
    """
    Mask credit card number for logging/display purposes.
    Returns only the last 4 digits.
    """
    card_str = str(card_number)
    if len(card_str) >= 4:
        return f"****-****-****-{card_str[-4:]}"
    return "****"


def log_payment_attempt(user_id: str, amount: float, crypto: str, card_last4: str, status: str):
    """
    Log payment attempt for audit purposes.
    """
    logger.info(
        f"Payment attempt - User: {user_id}, Amount: ${amount}, Crypto: {crypto}, "
        f"Card: {card_last4}, Status: {status}"
    )
