"""
SQLAlchemy domain models for Classroom Downloader API
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class DownloadStatus(str, PyEnum):
    """Download job status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """User model - stores Google account information"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Encrypted credentials (Fernet encrypted JSON)
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Profile info
    picture_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    courses: Mapped[list["Course"]] = relationship(
        "Course",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    download_jobs: Mapped[list["DownloadJob"]] = relationship(
        "DownloadJob",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class Course(Base):
    """Course model - represents a Google Classroom course"""
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    google_course_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Course state
    state: Mapped[str] = mapped_column(String(50), nullable=False)  # ACTIVE, ARCHIVED, etc

    # Owner info
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Course URLs
    alternate_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Sync tracking
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="courses")
    coursework: Mapped[list["Coursework"]] = relationship(
        "Coursework",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    download_jobs: Mapped[list["DownloadJob"]] = relationship(
        "DownloadJob",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name='{self.name}')>"


class Coursework(Base):
    """Coursework model - represents assignments/materials with video links"""
    __tablename__ = "coursework"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    google_coursework_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Coursework type and state
    work_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ASSIGNMENT, MATERIAL, etc
    state: Mapped[str] = mapped_column(String(50), nullable=False)  # PUBLISHED, DRAFT, DELETED

    # URLs
    alternate_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Due date (for assignments)
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="coursework")
    video_links: Mapped[list["VideoLink"]] = relationship(
        "VideoLink",
        back_populates="coursework",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Coursework(id={self.id}, title='{self.title}')>"


class VideoLink(Base):
    """VideoLink model - video URLs found in coursework"""
    __tablename__ = "video_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coursework_id: Mapped[int] = mapped_column(Integer, ForeignKey("coursework.id"), nullable=False)

    url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Video source type
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # youtube, drive, vimeo, etc

    # Drive specific fields
    drive_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    drive_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Download tracking
    is_downloaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    download_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    coursework: Mapped["Coursework"] = relationship("Coursework", back_populates="video_links")
    download_jobs: Mapped[list["DownloadJob"]] = relationship(
        "DownloadJob",
        back_populates="video_link",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VideoLink(id={self.id}, url='{self.url[:50]}...')>"


class DownloadJob(Base):
    """DownloadJob model - tracks video download tasks"""
    __tablename__ = "download_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    video_link_id: Mapped[int] = mapped_column(Integer, ForeignKey("video_links.id"), nullable=False)

    # Job status
    status: Mapped[DownloadStatus] = mapped_column(
        Enum(DownloadStatus),
        default=DownloadStatus.PENDING,
        nullable=False,
        index=True
    )

    # Progress tracking
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downloaded_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Output info
    output_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="download_jobs")
    course: Mapped["Course"] = relationship("Course", back_populates="download_jobs")
    video_link: Mapped["VideoLink"] = relationship("VideoLink", back_populates="download_jobs")

    def __repr__(self) -> str:
        return f"<DownloadJob(id={self.id}, status={self.status.value})>"
