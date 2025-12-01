"""
VideoLink repository for database operations
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import VideoLink
from app.repositories.base import BaseRepository


class VideoLinkRepository(BaseRepository[VideoLink]):
    """Repository for VideoLink model"""

    def __init__(self, db: AsyncSession):
        super().__init__(VideoLink, db)

    async def get_by_url(self, url: str) -> Optional[VideoLink]:
        """
        Get video link by URL

        Args:
            url: Video URL

        Returns:
            VideoLink instance or None
        """
        result = await self.db.execute(
            select(VideoLink).where(VideoLink.url == url)
        )
        return result.scalar_one_or_none()

    async def get_by_coursework(
        self,
        coursework_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[VideoLink]:
        """
        Get video links for a coursework

        Args:
            coursework_id: Coursework ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of video links
        """
        result = await self.db.execute(
            select(VideoLink)
            .where(VideoLink.coursework_id == coursework_id)
            .offset(skip)
            .limit(limit)
            .order_by(VideoLink.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_drive_file_id(
        self,
        drive_file_id: str,
    ) -> Optional[VideoLink]:
        """
        Get video link by Google Drive file ID

        Args:
            drive_file_id: Google Drive file ID

        Returns:
            VideoLink instance or None
        """
        result = await self.db.execute(
            select(VideoLink).where(VideoLink.drive_file_id == drive_file_id)
        )
        return result.scalar_one_or_none()

    async def get_not_downloaded(
        self,
        coursework_id: int,
    ) -> list[VideoLink]:
        """
        Get video links that haven't been downloaded

        Args:
            coursework_id: Coursework ID

        Returns:
            List of video links
        """
        result = await self.db.execute(
            select(VideoLink)
            .where(
                VideoLink.coursework_id == coursework_id,
                VideoLink.is_downloaded == False,
            )
            .order_by(VideoLink.created_at)
        )
        return list(result.scalars().all())

    async def mark_as_downloaded(
        self,
        video_link_id: int,
        download_path: str,
        file_size_bytes: int,
    ) -> Optional[VideoLink]:
        """
        Mark video link as downloaded

        Args:
            video_link_id: VideoLink ID
            download_path: Path where video was downloaded
            file_size_bytes: Size of downloaded file

        Returns:
            Updated video link or None
        """
        return await self.update(
            video_link_id,
            is_downloaded=True,
            download_path=download_path,
            file_size_bytes=file_size_bytes,
        )
