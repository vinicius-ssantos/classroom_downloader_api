"""
Cookie manager - armazena e gerencia cookies do usuário com criptografia
"""
import json
import re
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from app.core.logging import get_logger

logger = get_logger(__name__)


class CookieManager:
    """
    Gerencia cookies do usuário com criptografia Fernet

    Cookies são armazenados criptografados em disco para segurança
    """

    def __init__(
        self,
        cookies_file: Path = Path(".secrets/cookies.json"),
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize cookie manager

        Args:
            cookies_file: Path to cookies storage file
            encryption_key: Fernet encryption key (if None, cookies stored as plain JSON)
        """
        self.cookies_file = cookies_file
        self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
        self.encryption_key = encryption_key
        self.cipher = None

        if encryption_key:
            try:
                self.cipher = Fernet(encryption_key.encode())
                logger.info("cookie_manager_initialized", encryption_enabled=True)
            except Exception as e:
                logger.error(
                    "cookie_encryption_init_failed",
                    error=str(e),
                    exc_info=True,
                )
                raise ValueError(
                    "Invalid encryption key. Generate with: "
                    "python -c \"from cryptography.fernet import Fernet; "
                    "print(Fernet.generate_key().decode())\""
                )
        else:
            logger.warning(
                "cookie_manager_initialized",
                encryption_enabled=False,
                message="Cookies will be stored without encryption",
            )

    def save_cookies(self, cookies_dict: dict[str, str]) -> None:
        """
        Save cookies to file (encrypted if key provided)

        Args:
            cookies_dict: Dictionary of cookie name -> value
        """
        try:
            # Serialize to JSON
            plaintext = json.dumps(cookies_dict, indent=2)

            if self.cipher:
                # Encrypt
                encrypted = self.cipher.encrypt(plaintext.encode())
                self.cookies_file.write_bytes(encrypted)
                logger.info(
                    "cookies_saved",
                    count=len(cookies_dict),
                    encrypted=True,
                )
            else:
                # Save as plain JSON
                self.cookies_file.write_text(plaintext, encoding="utf-8")
                logger.warning(
                    "cookies_saved",
                    count=len(cookies_dict),
                    encrypted=False,
                    message="Cookies saved without encryption",
                )

        except Exception as e:
            logger.error("cookies_save_failed", error=str(e), exc_info=True)
            raise

    def load_cookies(self) -> Optional[dict[str, str]]:
        """
        Load cookies from file (decrypted if encrypted)

        Returns:
            Dictionary of cookie name -> value or None
        """
        try:
            if not self.cookies_file.exists():
                logger.warning(
                    "cookies_file_not_found",
                    file_path=str(self.cookies_file),
                )
                return None

            if self.cipher:
                # Read and decrypt
                encrypted = self.cookies_file.read_bytes()
                try:
                    plaintext = self.cipher.decrypt(encrypted).decode()
                except Exception as decrypt_error:
                    logger.error(
                        "cookies_decryption_failed",
                        error=str(decrypt_error),
                        message="Invalid encryption key or corrupted file",
                    )
                    return None
            else:
                # Read plain JSON
                plaintext = self.cookies_file.read_text(encoding="utf-8")

            cookies = json.loads(plaintext)
            logger.info(
                "cookies_loaded",
                count=len(cookies),
                encrypted=self.cipher is not None,
            )
            return cookies

        except Exception as e:
            logger.error("cookies_load_failed", error=str(e), exc_info=True)
            return None

    def parse_curl_cookies(self, curl_command: str) -> dict[str, str]:
        """
        Parse cookies from curl command

        Args:
            curl_command: Curl command with -b flag

        Returns:
            Dictionary of cookie name -> value
        """
        cookies = {}

        # Find -b flag with cookies
        cookie_match = re.search(r"-b\s+'([^']+)'", curl_command)
        if not cookie_match:
            cookie_match = re.search(r'-b\s+"([^"]+)"', curl_command)

        if not cookie_match:
            logger.warning("Nenhum cookie encontrado no comando curl")
            return cookies

        cookie_string = cookie_match.group(1)

        # Parse cookies (format: name=value; name2=value2)
        for cookie in cookie_string.split("; "):
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                cookies[name.strip()] = value.strip()

        logger.info("cookies_parsed", count=len(cookies))
        return cookies

    def parse_curl_file(self, curl_file: Path) -> dict[str, str]:
        """
        Parse cookies from curl file (multiple curl commands)

        Args:
            curl_file: Path to file with curl commands

        Returns:
            Dictionary of cookie name -> value (merged from all commands)
        """
        cookies = {}

        try:
            content = curl_file.read_text(encoding="utf-8")

            # Find all curl commands
            curl_commands = re.findall(r"curl\s+'[^']+'\s+(?:[^\n]+\n?)+", content)

            for curl_cmd in curl_commands:
                cmd_cookies = self.parse_curl_cookies(curl_cmd)
                cookies.update(cmd_cookies)

            logger.info("cookies_parsed_from_file", unique_count=len(cookies))
            return cookies

        except Exception as e:
            logger.error("curl_file_parse_failed", error=str(e), exc_info=True)
            return {}

    def get_cookie_dict(self) -> dict[str, str]:
        """
        Get cookies as dictionary for httpx

        Returns:
            Dictionary of cookie name -> value
        """
        cookies = self.load_cookies()
        return cookies or {}

    def has_cookies(self) -> bool:
        """
        Check if cookies are available

        Returns:
            True if cookies exist
        """
        return self.cookies_file.exists()


# Singleton instance
_cookie_manager: Optional[CookieManager] = None


def get_cookie_manager(encryption_key: Optional[str] = None) -> CookieManager:
    """
    Get singleton cookie manager instance

    Args:
        encryption_key: Fernet encryption key (optional, uses from settings if None)

    Returns:
        CookieManager instance
    """
    global _cookie_manager
    if _cookie_manager is None:
        # Get encryption key from settings if not provided
        if encryption_key is None:
            try:
                from app.core.config import get_settings

                settings = get_settings()
                encryption_key = settings.encryption_key
            except Exception:
                # Settings not available (e.g., in tests), use without encryption
                pass

        _cookie_manager = CookieManager(encryption_key=encryption_key)
    return _cookie_manager
