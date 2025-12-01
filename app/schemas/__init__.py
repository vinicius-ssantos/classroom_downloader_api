"""Schemas module - exports all Pydantic schemas"""
from app.schemas.auth import (
    AuthCallbackRequest,
    AuthCallbackResponse,
    AuthURLResponse,
    CredentialsStatusResponse,
    TokenResponse,
)
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseSummary,
    CourseUpdate,
)
from app.schemas.coursework import (
    CourseworkCreate,
    CourseworkResponse,
    CourseworkUpdate,
    CourseworkWithVideos,
)
from app.schemas.download import (
    DownloadBatchResponse,
    DownloadJobCreate,
    DownloadJobResponse,
    DownloadJobUpdate,
    DownloadJobWithDetails,
    DownloadRequest,
)
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserWithCredentials,
)
from app.schemas.video_link import (
    VideoLinkCreate,
    VideoLinkResponse,
    VideoLinkUpdate,
)

__all__ = [
    # Auth
    "AuthURLResponse",
    "AuthCallbackRequest",
    "AuthCallbackResponse",
    "TokenResponse",
    "CredentialsStatusResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserWithCredentials",
    # Course
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "CourseSummary",
    # Coursework
    "CourseworkCreate",
    "CourseworkUpdate",
    "CourseworkResponse",
    "CourseworkWithVideos",
    # VideoLink
    "VideoLinkCreate",
    "VideoLinkUpdate",
    "VideoLinkResponse",
    # Download
    "DownloadJobCreate",
    "DownloadJobUpdate",
    "DownloadJobResponse",
    "DownloadJobWithDetails",
    "DownloadRequest",
    "DownloadBatchResponse",
]
