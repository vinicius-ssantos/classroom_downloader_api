"""
Download job schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import DownloadStatus


class DownloadJobBase(BaseModel):
    """Base download job schema"""
    pass


class DownloadJobCreate(DownloadJobBase):
    """Schema for creating a download job"""
    user_id: int
    course_id: int
    video_link_id: int


class DownloadJobUpdate(BaseModel):
    """Schema for updating a download job"""
    status: Optional[DownloadStatus] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    downloaded_bytes: Optional[int] = Field(None, ge=0)
    total_bytes: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    output_path: Optional[str] = Field(None, max_length=1024)
    file_size_bytes: Optional[int] = Field(None, ge=0)


class DownloadJobResponse(DownloadJobBase):
    """Schema for download job response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    video_link_id: int
    status: DownloadStatus
    progress_percent: int
    downloaded_bytes: int
    total_bytes: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int
    output_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DownloadJobWithDetails(DownloadJobResponse):
    """Schema for download job with related details"""
    video_url: str = Field(..., description="URL of the video being downloaded")
    video_title: Optional[str] = Field(None, description="Title of the video")
    course_name: str = Field(..., description="Name of the course")
    coursework_title: str = Field(..., description="Title of the coursework")


class DownloadRequest(BaseModel):
    """Schema for requesting a download"""
    video_link_ids: list[int] = Field(..., min_length=1, description="List of video link IDs to download")


class DownloadBatchResponse(BaseModel):
    """Schema for batch download response"""
    created_jobs: list[DownloadJobResponse] = Field(default_factory=list)
    failed_jobs: list[dict[str, str]] = Field(default_factory=list, description="Failed job creation details")
    total_requested: int
    total_created: int
    total_failed: int
