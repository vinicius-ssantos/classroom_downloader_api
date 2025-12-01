"""
Base repository with generic CRUD operations
"""
from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with generic CRUD operations"""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    async def get(self, id: int) -> Optional[ModelType]:
        """
        Get a record by ID

        Args:
            id: Record ID

        Returns:
            Model instance or None
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get all records with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record

        Args:
            **kwargs: Model fields

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs: Any) -> Optional[ModelType]:
        """
        Update a record

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None
        """
        instance = await self.get(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Delete a record

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get(id)
        if not instance:
            return False

        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def count(self) -> int:
        """
        Count total records

        Returns:
            Total number of records
        """
        result = await self.db.execute(
            select(self.model).with_only_columns(func.count())
        )
        return result.scalar_one()
