"""
User repository for database operations
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User instance or None
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Get user by Google ID

        Args:
            google_id: Google user ID

        Returns:
            User instance or None
        """
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def update_credentials(
        self,
        user_id: int,
        encrypted_credentials: str,
    ) -> Optional[User]:
        """
        Update user credentials

        Args:
            user_id: User ID
            encrypted_credentials: Encrypted credentials string

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            encrypted_credentials=encrypted_credentials,
        )

    async def update_last_login(self, user_id: int) -> Optional[User]:
        """
        Update user's last login timestamp

        Args:
            user_id: User ID

        Returns:
            Updated user or None
        """
        from datetime import datetime
        return await self.update(user_id, last_login=datetime.utcnow())
