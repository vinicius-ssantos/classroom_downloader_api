"""
Course schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseBase(BaseModel):
    """Base course schema"""
    name: str = Field(..., min_length=1, max_length=512)
    section: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    room: Optional[str] = Field(None, max_length=255)


class CourseCreate(CourseBase):
    """Schema for creating a course"""
    google_course_id: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., max_length=50)
    alternate_link: Optional[str] = Field(None, max_length=512)


class CourseUpdate(BaseModel):
    """Schema for updating a course"""
    name: Optional[str] = Field(None, min_length=1, max_length=512)
    section: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    room: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=50)


class CourseResponse(CourseBase):
    """Schema for course response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    google_course_id: str
    state: str
    alternate_link: Optional[str] = None
    owner_id: int
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CourseSummary(BaseModel):
    """Schema for course summary with stats"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    google_course_id: str
    name: str
    state: str
    coursework_count: int = Field(default=0, description="Number of coursework items")
    video_count: int = Field(default=0, description="Number of video links")
    downloaded_count: int = Field(default=0, description="Number of downloaded videos")
