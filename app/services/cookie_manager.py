"""
Cookie manager - armazena e gerencia cookies do usuário
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CookieManager:
    """Gerencia cookies do usuário"""

    def __init__(self, cookies_file: Path = Path(".secrets/cookies.json")):
        """
        Initialize cookie manager

        Args:
            cookies_file: Path to cookies storage file
        """
        self.cookies_file = cookies_file
        self.cookies_file.parent.mkdir(parents=True, exist_ok=True)

    def save_cookies(self, cookies_dict: dict[str, str]) -> None:
        """
        Save cookies to file

        Args:
            cookies_dict: Dictionary of cookie name -> value
        """
        try:
            with open(self.cookies_file, "w") as f:
                json.dump(cookies_dict, f, indent=2)
            logger.info(f"Cookies salvos: {len(cookies_dict)} cookies")
        except Exception as e:
            logger.error(f"Erro ao salvar cookies: {e}")
            raise

    def load_cookies(self) -> Optional[dict[str, str]]:
        """
        Load cookies from file

        Returns:
            Dictionary of cookie name -> value or None
        """
        try:
            if not self.cookies_file.exists():
                logger.warning(f"Arquivo de cookies não encontrado: {self.cookies_file}")
                return None

            with open(self.cookies_file, "r") as f:
                cookies = json.load(f)
            logger.info(f"Cookies carregados: {len(cookies)} cookies")
            return cookies
        except Exception as e:
            logger.error(f"Erro ao carregar cookies: {e}")
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

        logger.info(f"Cookies parseados: {len(cookies)} cookies")
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

            logger.info(f"Total de cookies únicos: {len(cookies)}")
            return cookies

        except Exception as e:
            logger.error(f"Erro ao ler arquivo curl: {e}")
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


def get_cookie_manager() -> CookieManager:
    """
    Get singleton cookie manager instance

    Returns:
        CookieManager instance
    """
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager
