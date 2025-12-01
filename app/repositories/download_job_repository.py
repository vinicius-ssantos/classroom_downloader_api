"""
DownloadJob repository for database operations
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Course, Coursework, DownloadJob, DownloadStatus, VideoLink
from app.repositories.base import BaseRepository


class DownloadJobRepository(BaseRepository[DownloadJob]):
    """Repository for DownloadJob model"""

    def __init__(self, db: AsyncSession):
        super().__init__(DownloadJob, db)

    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DownloadJob]:
        """
        Get download jobs for a user

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of download jobs
        """
        result = await self.db.execute(
            select(DownloadJob)
            .where(DownloadJob.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(DownloadJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_course(
        self,
        course_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DownloadJob]:
        """
        Get download jobs for a course

        Args:
            course_id: Course ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of download jobs
        """
        result = await self.db.execute(
            select(DownloadJob)
            .where(DownloadJob.course_id == course_id)
            .offset(skip)
            .limit(limit)
            .order_by(DownloadJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: DownloadStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DownloadJob]:
        """
        Get download jobs by status

        Args:
            status: Download status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of download jobs
        """
        result = await self.db.execute(
            select(DownloadJob)
            .where(DownloadJob.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(DownloadJob.created_at)
        )
        return list(result.scalars().all())

    async def get_with_details(self, job_id: int) -> Optional[dict]:
        """
        Get download job with related details

        Args:
            job_id: Download job ID

        Returns:
            Job with details dictionary or None
        """
        result = await self.db.execute(
            select(
                DownloadJob,
                VideoLink.url,
                VideoLink.title,
                Course.name,
                Coursework.title,
            )
            .join(VideoLink, DownloadJob.video_link_id == VideoLink.id)
            .join(Course, DownloadJob.course_id == Course.id)
            .join(Coursework, VideoLink.coursework_id == Coursework.id)
            .where(DownloadJob.id == job_id)
        )
        row = result.first()
        if not row:
            return None

        job, video_url, video_title, course_name, coursework_title = row
        return {
            "job": job,
            "video_url": video_url,
            "video_title": video_title,
            "course_name": course_name,
            "coursework_title": coursework_title,
        }

    async def update_status(
        self,
        job_id: int,
        status: DownloadStatus,
        error_message: Optional[str] = None,
    ) -> Optional[DownloadJob]:
        """
        Update job status

        Args:
            job_id: Download job ID
            status: New status
            error_message: Optional error message

        Returns:
            Updated job or None
        """
        update_data = {"status": status}

        if status == DownloadStatus.DOWNLOADING:
            update_data["started_at"] = datetime.utcnow()
        elif status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            update_data["completed_at"] = datetime.utcnow()

        if error_message:
            update_data["error_message"] = error_message

        return await self.update(job_id, **update_data)

    async def update_progress(
        self,
        job_id: int,
        progress_percent: int,
        downloaded_bytes: int,
        total_bytes: Optional[int] = None,
    ) -> Optional[DownloadJob]:
        """
        Update job progress

        Args:
            job_id: Download job ID
            progress_percent: Progress percentage (0-100)
            downloaded_bytes: Bytes downloaded
            total_bytes: Total bytes (optional)

        Returns:
            Updated job or None
        """
        update_data = {
            "progress_percent": progress_percent,
            "downloaded_bytes": downloaded_bytes,
        }
        if total_bytes is not None:
            update_data["total_bytes"] = total_bytes

        return await self.update(job_id, **update_data)

    async def increment_retry_count(self, job_id: int) -> Optional[DownloadJob]:
        """
        Increment retry count

        Args:
            job_id: Download job ID

        Returns:
            Updated job or None
        """
        job = await self.get(job_id)
        if not job:
            return None

        return await self.update(job_id, retry_count=job.retry_count + 1)
