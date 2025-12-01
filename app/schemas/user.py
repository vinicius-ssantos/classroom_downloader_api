"""
User schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user"""
    google_id: str = Field(..., min_length=1, max_length=255)
    picture_url: Optional[str] = Field(None, max_length=512)


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    picture_url: Optional[str] = Field(None, max_length=512)


class UserResponse(UserBase):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    google_id: str
    picture_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserWithCredentials(UserResponse):
    """Schema for user with credential status"""
    has_credentials: bool = Field(..., description="Whether user has stored credentials")
