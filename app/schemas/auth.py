"""
Authentication schemas for API requests and responses
"""
from typing import Optional

from pydantic import BaseModel, Field


class AuthURLResponse(BaseModel):
    """Schema for OAuth2 authorization URL response"""
    auth_url: str = Field(..., description="Google OAuth2 authorization URL")
    state: str = Field(..., description="State parameter for CSRF protection")


class AuthCallbackRequest(BaseModel):
    """Schema for OAuth2 callback request"""
    code: str = Field(..., description="Authorization code from Google")
    state: str = Field(..., description="State parameter for verification")


class AuthCallbackResponse(BaseModel):
    """Schema for OAuth2 callback response"""
    success: bool
    message: str
    user_id: Optional[int] = None
    user_email: Optional[str] = None


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class CredentialsStatusResponse(BaseModel):
    """Schema for credentials status response"""
    has_credentials: bool
    is_expired: bool = Field(default=False, description="Whether credentials are expired")
    scopes: list[str] = Field(default_factory=list, description="Authorized scopes")
