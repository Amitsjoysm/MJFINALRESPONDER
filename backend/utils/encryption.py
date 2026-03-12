"""Secure encryption utilities for sensitive data"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """Encryption service using Fernet (symmetric encryption)"""
    
    def __init__(self, secret_key: str = None):
        if secret_key:
            # Derive key from secret
            self.key = self._derive_key(secret_key.encode())
        else:
            # Generate new key
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, secret: bytes) -> bytes:
        """Derive encryption key from secret using PBKDF2"""
        salt = b'email_assistant_salt_v1'  # In production, use random salt per user
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt string"""
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt string"""
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def get_key_string(self) -> str:
        """Get key as string for storage"""
        return self.key.decode()

# Global encryption service
encryption_service = None

def initialize_encryption(secret_key: str):
    """Initialize global encryption service"""
    global encryption_service
    encryption_service = EncryptionService(secret_key)
    return encryption_service

def get_encryption_service() -> EncryptionService:
    """Get global encryption service"""
    if encryption_service is None:
        raise RuntimeError("Encryption service not initialized")
    return encryption_service
