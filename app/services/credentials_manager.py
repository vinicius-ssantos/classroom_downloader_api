"""
Credentials manager for encrypting/decrypting Google OAuth2 credentials
"""
import json
import logging
from typing import Any, Optional

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CredentialsManager:
    """Manager for encrypting and decrypting Google OAuth2 credentials"""

    def __init__(self):
        """Initialize with encryption key from settings"""
        try:
            self.cipher = Fernet(settings.encryption_key.encode())
        except Exception as e:
            logger.error(f"Failed to initialize Fernet cipher: {e}")
            raise ValueError("Invalid encryption key. Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")

    def encrypt_credentials(self, credentials: Credentials) -> str:
        """
        Encrypt Google OAuth2 credentials

        Args:
            credentials: Google OAuth2 Credentials object

        Returns:
            Encrypted credentials as base64 string
        """
        try:
            # Convert credentials to dictionary
            creds_dict = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }

            # Serialize to JSON
            creds_json = json.dumps(creds_dict)

            # Encrypt
            encrypted = self.cipher.encrypt(creds_json.encode())

            return encrypted.decode()

        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise

    def decrypt_credentials(self, encrypted_credentials: str) -> Optional[Credentials]:
        """
        Decrypt Google OAuth2 credentials

        Args:
            encrypted_credentials: Encrypted credentials string

        Returns:
            Google OAuth2 Credentials object or None if decryption fails
        """
        try:
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_credentials.encode())

            # Parse JSON
            creds_dict = json.loads(decrypted.decode())

            # Reconstruct Credentials object
            credentials = Credentials(
                token=creds_dict["token"],
                refresh_token=creds_dict["refresh_token"],
                token_uri=creds_dict["token_uri"],
                client_id=creds_dict["client_id"],
                client_secret=creds_dict["client_secret"],
                scopes=creds_dict["scopes"],
            )

            return credentials

        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return None

    def credentials_to_dict(self, credentials: Credentials) -> dict[str, Any]:
        """
        Convert Credentials object to dictionary (for API responses)

        Args:
            credentials: Google OAuth2 Credentials object

        Returns:
            Dictionary representation (without sensitive data)
        """
        return {
            "scopes": credentials.scopes,
            "token_uri": credentials.token_uri,
            "has_refresh_token": bool(credentials.refresh_token),
            "expired": credentials.expired,
            "valid": credentials.valid,
        }


# Singleton instance
_credentials_manager: Optional[CredentialsManager] = None


def get_credentials_manager() -> CredentialsManager:
    """
    Get singleton credentials manager instance

    Returns:
        CredentialsManager instance
    """
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = CredentialsManager()
    return _credentials_manager
