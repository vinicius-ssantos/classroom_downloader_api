"""
VideoLink schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class VideoLinkBase(BaseModel):
    """Base video link schema"""
    url: str = Field(..., max_length=1024)
    title: Optional[str] = Field(None, max_length=512)
    source_type: str = Field(..., max_length=50)


class VideoLinkCreate(VideoLinkBase):
    """Schema for creating a video link"""
    coursework_id: int
    drive_file_id: Optional[str] = Field(None, max_length=255)
    drive_mime_type: Optional[str] = Field(None, max_length=100)


class VideoLinkUpdate(BaseModel):
    """Schema for updating a video link"""
    title: Optional[str] = Field(None, max_length=512)
    is_downloaded: Optional[bool] = None
    download_path: Optional[str] = Field(None, max_length=1024)
    file_size_bytes: Optional[int] = None


class VideoLinkResponse(VideoLinkBase):
    """Schema for video link response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    coursework_id: int
    drive_file_id: Optional[str] = None
    drive_mime_type: Optional[str] = None
    is_downloaded: bool
    download_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime
    updated_at: datetime
