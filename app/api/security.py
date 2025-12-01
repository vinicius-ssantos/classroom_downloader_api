"""
Security dependencies for API endpoints
"""
from fastapi import HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def require_admin_token(
    request: Request,
    settings: Settings = None,
) -> None:
    """
    Dependency to require admin token for sensitive operations

    Usage:
        @router.post("/sensitive-endpoint")
        async def my_endpoint(
            _: None = Depends(require_admin_token),
        ):
            # Your code here
            pass

    Args:
        request: FastAPI request
        settings: Application settings

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if settings is None:
        settings = get_settings()

    # If no admin token is configured, allow access (development mode)
    expected_token = settings.admin_api_token
    if not expected_token:
        logger.warning(
            "admin_token_not_configured",
            message="Admin token not configured - allowing access",
            path=request.url.path,
        )
        return

    # Check for token in header
    provided_token = request.headers.get("x-admin-token")

    if not provided_token:
        logger.warning(
            "admin_token_missing",
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token required. Provide X-Admin-Token header.",
        )

    # Validate token
    if provided_token != expected_token:
        logger.warning(
            "admin_token_invalid",
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )

    # Token is valid
    logger.info(
        "admin_access_granted",
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )


def get_request_actor(request: Request) -> str:
    """
    Get the actor (user/IP) making the request for audit logging

    Checks X-Admin-Actor header first, falls back to client IP

    Args:
        request: FastAPI request

    Returns:
        Actor identifier (username or IP address)
    """
    # Check for explicit actor header
    actor = request.headers.get("x-admin-actor")
    if actor:
        return actor

    # Fall back to client IP
    if request.client:
        return request.client.host

    return "unknown"
