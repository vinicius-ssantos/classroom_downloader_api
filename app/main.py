"""
FastAPI application entry point for Classroom Downloader API
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.api.middleware.logging import RequestLoggingMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import close_db, init_db
from app.workers import get_download_worker

settings = get_settings()

# Configure structured logging
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    log_redact_fields=settings.log_redact_fields,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("app_starting", environment=settings.environment)

    # Initialize database
    logger.info("database_initializing")
    await init_db()
    logger.info("database_initialized")

    # Start background worker
    worker = get_download_worker()
    worker_task = asyncio.create_task(worker.start())
    logger.info("worker_started")

    yield

    # Shutdown
    logger.info("app_shutting_down")

    # Stop worker
    logger.info("worker_stopping")
    await worker.stop()
    worker_task.cancel()
    logger.info("worker_stopped")

    # Close database
    logger.info("database_closing")
    await close_db()
    logger.info("database_closed")

    logger.info("app_shutdown_complete")


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

    # HTTPS redirect in production
    if settings.force_https_redirect or (
        settings.force_https_redirect is None
        and settings.environment == "production"
    ):
        app.add_middleware(HTTPSRedirectMiddleware)
        logger.info("https_redirect_enabled")

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # CORS middleware - configured by environment
    cors_origins = settings.allowed_cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(
        "cors_configured",
        origins=cors_origins if cors_origins else ["*"],
        environment=settings.environment,
    )

    # Register routers
    from app.api.routers import courses_simple, downloads, health
    app.include_router(health.router)
    # app.include_router(auth.router)  # OAuth2 desabilitado - usando cookies
    app.include_router(courses_simple.router)
    app.include_router(downloads.router)

    @app.get("/")
    async def root():
        return {
            "message": "Classroom Downloader API",
            "version": settings.app_version,
            "docs": "/docs",
            "environment": settings.environment,
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
