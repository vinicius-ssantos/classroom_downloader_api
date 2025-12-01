"""
Authentication router for Google OAuth2
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthCallbackResponse,
    AuthURLResponse,
    CredentialsStatusResponse,
)
from app.services.credentials_manager import get_credentials_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


def create_oauth_flow() -> Flow:
    """
    Create Google OAuth2 flow

    Returns:
        Configured Flow object
    """
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=settings.google_scopes,
        redirect_uri=settings.google_redirect_uri,
    )


@router.get("/url", response_model=AuthURLResponse)
async def get_auth_url():
    """
    Get Google OAuth2 authorization URL

    Returns:
        Authorization URL and state parameter
    """
    try:
        flow = create_oauth_flow()
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        return AuthURLResponse(auth_url=auth_url, state=state)

    except Exception as e:
        logger.error(f"Failed to create auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create authorization URL",
        )


@router.get("/callback", response_model=AuthCallbackResponse)
async def auth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth2 callback from Google

    Args:
        code: Authorization code
        state: State parameter
        db: Database session

    Returns:
        Authentication result
    """
    try:
        # Exchange code for credentials
        flow = create_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info from Google
        from googleapiclient.discovery import build
        oauth2_service = build("oauth2", "v2", credentials=credentials)
        user_info = oauth2_service.userinfo().get().execute()

        google_id = user_info["id"]
        email = user_info["email"]
        name = user_info.get("name", email)
        picture_url = user_info.get("picture")

        # Get or create user
        user_repo = UserRepository(db)
        user = await user_repo.get_by_google_id(google_id)

        if user:
            # Update existing user
            await user_repo.update(
                user.id,
                name=name,
                picture_url=picture_url,
            )
            await user_repo.update_last_login(user.id)
        else:
            # Create new user
            user = await user_repo.create(
                email=email,
                name=name,
                google_id=google_id,
                picture_url=picture_url,
            )

        # Encrypt and store credentials
        creds_manager = get_credentials_manager()
        encrypted_creds = creds_manager.encrypt_credentials(credentials)
        await user_repo.update_credentials(user.id, encrypted_creds)

        await db.commit()

        return AuthCallbackResponse(
            success=True,
            message="Authentication successful",
            user_id=user.id,
            user_email=user.email,
        )

    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/status/{user_id}", response_model=CredentialsStatusResponse)
async def get_credentials_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's credentials status

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Credentials status
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.encrypted_credentials:
            return CredentialsStatusResponse(
                has_credentials=False,
                is_expired=True,
                scopes=[],
            )

        # Decrypt credentials
        creds_manager = get_credentials_manager()
        credentials = creds_manager.decrypt_credentials(user.encrypted_credentials)

        if not credentials:
            return CredentialsStatusResponse(
                has_credentials=False,
                is_expired=True,
                scopes=[],
            )

        # Check if expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                # Update stored credentials
                encrypted_creds = creds_manager.encrypt_credentials(credentials)
                await user_repo.update_credentials(user.id, encrypted_creds)
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                return CredentialsStatusResponse(
                    has_credentials=True,
                    is_expired=True,
                    scopes=credentials.scopes or [],
                )

        return CredentialsStatusResponse(
            has_credentials=True,
            is_expired=credentials.expired,
            scopes=credentials.scopes or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credentials status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get credentials status",
        )


async def get_user_credentials(
    user_id: int,
    db: AsyncSession,
) -> Optional[Credentials]:
    """
    Dependency to get user credentials

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Google OAuth2 credentials or None

    Raises:
        HTTPException: If user not found or no credentials
    """
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.encrypted_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials found. Please authenticate first.",
        )

    creds_manager = get_credentials_manager()
    credentials = creds_manager.decrypt_credentials(user.encrypted_credentials)

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please re-authenticate.",
        )

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            # Update stored credentials
            encrypted_creds = creds_manager.encrypt_credentials(credentials)
            await user_repo.update_credentials(user.id, encrypted_creds)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credentials expired and refresh failed. Please re-authenticate.",
            )

    return credentials
