"""
Course repository for database operations
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Course, Coursework, VideoLink
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    """Repository for Course model"""

    def __init__(self, db: AsyncSession):
        super().__init__(Course, db)

    async def get_by_google_course_id(
        self,
        google_course_id: str,
    ) -> Optional[Course]:
        """
        Get course by Google course ID

        Args:
            google_course_id: Google Classroom course ID

        Returns:
            Course instance or None
        """
        result = await self.db.execute(
            select(Course).where(Course.google_course_id == google_course_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Course]:
        """
        Get courses for a user

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of courses
        """
        result = await self.db.execute(
            select(Course)
            .where(Course.owner_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Course.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_coursework(self, course_id: int) -> Optional[Course]:
        """
        Get course with related coursework loaded

        Args:
            course_id: Course ID

        Returns:
            Course with coursework or None
        """
        result = await self.db.execute(
            select(Course)
            .where(Course.id == course_id)
            .options(selectinload(Course.coursework))
        )
        return result.scalar_one_or_none()

    async def get_summary(self, user_id: int) -> list[dict]:
        """
        Get course summaries with video counts

        Args:
            user_id: User ID

        Returns:
            List of course summary dictionaries
        """
        query = (
            select(
                Course.id,
                Course.google_course_id,
                Course.name,
                Course.state,
                func.count(func.distinct(Coursework.id)).label("coursework_count"),
                func.count(func.distinct(VideoLink.id)).label("video_count"),
                func.sum(
                    func.cast(VideoLink.is_downloaded, func.Integer)
                ).label("downloaded_count"),
            )
            .where(Course.owner_id == user_id)
            .outerjoin(Coursework, Coursework.course_id == Course.id)
            .outerjoin(VideoLink, VideoLink.coursework_id == Coursework.id)
            .group_by(Course.id)
        )

        result = await self.db.execute(query)
        return [dict(row._mapping) for row in result]

    async def update_last_synced(self, course_id: int) -> Optional[Course]:
        """
        Update course's last synced timestamp

        Args:
            course_id: Course ID

        Returns:
            Updated course or None
        """
        return await self.update(
            course_id,
            last_synced_at=datetime.utcnow(),
        )
