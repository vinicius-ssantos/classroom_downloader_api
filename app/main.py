"""
FastAPI application entry point for Classroom Downloader API
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db import close_db, init_db
from app.workers import get_download_worker

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    # Initialize database
    await init_db()

    # Start background worker
    worker = get_download_worker()
    worker_task = asyncio.create_task(worker.start())

    yield

    # Shutdown
    # Stop worker
    await worker.stop()
    worker_task.cancel()

    # Close database
    await close_db()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description="API para download automatizado de vídeos do Google Classroom",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.api.routers import auth, courses, downloads, health
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(courses.router)
    app.include_router(downloads.router)

    @app.get("/")
    async def root():
        return {
            "message": "Classroom Downloader API",
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
