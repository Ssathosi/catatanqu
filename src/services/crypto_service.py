"""
Bot Catatan Keuangan AI - Crypto Service
Handles encryption/decryption of sensitive data.
"""
import base64
import hashlib
from cryptography.fernet import Fernet
import bcrypt

from config import config


class CryptoService:
    """Service for encryption and hashing operations."""
    
    def __init__(self):
        # Create Fernet key from encryption key (must be 32 bytes base64 encoded)
        key = self._derive_key(config.ENCRYPTION_KEY)
        self.fernet = Fernet(key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive a valid Fernet key from any password."""
        # Use SHA256 to get 32 bytes, then base64 encode
        key_bytes = hashlib.sha256(password.encode()).digest()
        return base64.urlsafe_b64encode(key_bytes)
    
    # ==================== ENCRYPTION ====================
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        encrypted = self.fernet.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string data."""
        decrypted = self.fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def encrypt_amount(self, amount: int) -> str:
        """Encrypt monetary amount."""
        return self.encrypt(str(amount))
    
    def decrypt_amount(self, encrypted_amount: str) -> int:
        """Decrypt encrypted monetary amount."""
        decrypted = self.decrypt(encrypted_amount)
        return int(decrypted)
    
    # ==================== HASHING (for PIN) ====================
    
    def hash_pin(self, pin: str) -> str:
        """Hash PIN using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pin.encode(), salt)
        return hashed.decode()
    
    def verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify PIN against hash."""
        try:
            return bcrypt.checkpw(pin.encode(), pin_hash.encode())
        except Exception:
            return False


# Singleton instance
crypto = CryptoService()
