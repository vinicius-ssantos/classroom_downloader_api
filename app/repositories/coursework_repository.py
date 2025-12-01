"""
Coursework repository for database operations
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Coursework
from app.repositories.base import BaseRepository


class CourseworkRepository(BaseRepository[Coursework]):
    """Repository for Coursework model"""

    def __init__(self, db: AsyncSession):
        super().__init__(Coursework, db)

    async def get_by_google_coursework_id(
        self,
        google_coursework_id: str,
    ) -> Optional[Coursework]:
        """
        Get coursework by Google coursework ID

        Args:
            google_coursework_id: Google Classroom coursework ID

        Returns:
            Coursework instance or None
        """
        result = await self.db.execute(
            select(Coursework).where(
                Coursework.google_coursework_id == google_coursework_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_course(
        self,
        course_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Coursework]:
        """
        Get coursework for a course

        Args:
            course_id: Course ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of coursework
        """
        result = await self.db.execute(
            select(Coursework)
            .where(Coursework.course_id == course_id)
            .offset(skip)
            .limit(limit)
            .order_by(Coursework.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_videos(self, coursework_id: int) -> Optional[Coursework]:
        """
        Get coursework with related video links loaded

        Args:
            coursework_id: Coursework ID

        Returns:
            Coursework with video links or None
        """
        result = await self.db.execute(
            select(Coursework)
            .where(Coursework.id == coursework_id)
            .options(selectinload(Coursework.video_links))
        )
        return result.scalar_one_or_none()

    async def get_all_with_videos_by_course(
        self,
        course_id: int,
    ) -> list[Coursework]:
        """
        Get all coursework with video links for a course

        Args:
            course_id: Course ID

        Returns:
            List of coursework with video links
        """
        result = await self.db.execute(
            select(Coursework)
            .where(Coursework.course_id == course_id)
            .options(selectinload(Coursework.video_links))
            .order_by(Coursework.updated_at.desc())
        )
        return list(result.scalars().all())
