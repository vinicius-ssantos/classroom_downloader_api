"""
HTTP Client com cookies para acessar Google APIs sem OAuth2
"""
import logging
from typing import Any, Optional

import httpx

from app.services.cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class GoogleHTTPClient:
    """Cliente HTTP para acessar Google com cookies"""

    def __init__(self):
        """Initialize HTTP client"""
        self.cookie_manager = get_cookie_manager()
        self.cookies = self.cookie_manager.get_cookie_dict()

        # Headers padrão que imitam o navegador
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://classroom.google.com/",
            "Origin": "https://classroom.google.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    async def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make GET request

        Args:
            url: URL to request
            params: Query parameters
            **kwargs: Additional httpx options

        Returns:
            httpx Response
        """
        async with httpx.AsyncClient(cookies=self.cookies, timeout=30.0) as client:
            response = await client.get(
                url,
                params=params,
                headers=self.headers,
                **kwargs,
            )
            response.raise_for_status()
            return response

    async def post(
        self,
        url: str,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make POST request

        Args:
            url: URL to request
            json: JSON body
            data: Form data
            **kwargs: Additional httpx options

        Returns:
            httpx Response
        """
        async with httpx.AsyncClient(cookies=self.cookies, timeout=30.0) as client:
            response = await client.post(
                url,
                json=json,
                data=data,
                headers=self.headers,
                **kwargs,
            )
            response.raise_for_status()
            return response


# Singleton
_http_client: Optional[GoogleHTTPClient] = None


def get_http_client() -> GoogleHTTPClient:
    """
    Get singleton HTTP client

    Returns:
        GoogleHTTPClient instance
    """
    global _http_client
    if _http_client is None:
        _http_client = GoogleHTTPClient()
    return _http_client
