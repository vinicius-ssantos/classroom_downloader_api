"""
Coursework schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseworkBase(BaseModel):
    """Base coursework schema"""
    title: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = None


class CourseworkCreate(CourseworkBase):
    """Schema for creating coursework"""
    google_coursework_id: str = Field(..., min_length=1, max_length=255)
    course_id: int
    work_type: str = Field(..., max_length=50)
    state: str = Field(..., max_length=50)
    alternate_link: Optional[str] = Field(None, max_length=512)
    due_date: Optional[datetime] = None


class CourseworkUpdate(BaseModel):
    """Schema for updating coursework"""
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = None
    state: Optional[str] = Field(None, max_length=50)


class CourseworkResponse(CourseworkBase):
    """Schema for coursework response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    google_coursework_id: str
    course_id: int
    work_type: str
    state: str
    alternate_link: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CourseworkWithVideos(CourseworkResponse):
    """Schema for coursework with video links"""
    video_links: list["VideoLinkResponse"] = Field(default_factory=list)


# Forward reference resolution
from app.schemas.video_link import VideoLinkResponse
CourseworkWithVideos.model_rebuild()
