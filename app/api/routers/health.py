"""
Health check router
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("")
async def health_check():
    """
    Basic health check endpoint

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """
    Database health check endpoint

    Args:
        db: Database session

    Returns:
        Database health status
    """
    try:
        # Simple query to check database connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
