"""
Pytest configuration and shared fixtures
"""
import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.domain.models import Base
from app.main import create_app


# Pytest configuration for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_settings(tmp_path: Path) -> Settings:
    """
    Test-specific settings with in-memory database and temporary directories

    Returns:
        Settings instance configured for testing
    """
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(exist_ok=True)

    return Settings(
        # Application
        app_name="Classroom Downloader API - Test",
        app_version="1.0.0-test",
        debug=True,
        host="0.0.0.0",
        port=8001,

        # Database - use SQLite in-memory for tests
        database_url="sqlite+aiosqlite:///:memory:",

        # Google OAuth2 - dummy values for tests
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        google_redirect_uri="http://localhost:8001/auth/callback",

        # Security - test key (32 bytes base64)
        encryption_key="test-key-exactly-32-bytes-long",

        # Downloads
        download_dir=str(download_dir),
        max_concurrent_downloads=2,  # Lower for tests
        download_timeout_seconds=60,

        # Workers
        worker_poll_interval_seconds=1,  # Faster for tests
        worker_max_retries=2,  # Lower for tests

        # Logging
        log_level="DEBUG",
    )


@pytest_asyncio.fixture
async def async_engine(test_settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create async SQLAlchemy engine for tests

    Uses in-memory SQLite database that is created fresh for each test

    Args:
        test_settings: Test configuration

    Yields:
        AsyncEngine instance
    """
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,  # Set to True for SQL debugging
        connect_args={"check_same_thread": False},  # SQLite specific
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables and dispose
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_factory(
    async_engine: AsyncEngine,
) -> sessionmaker:
    """
    Create async session factory for tests

    Args:
        async_engine: Database engine

    Returns:
        Session factory
    """
    return sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def db_session(
    async_session_factory: sessionmaker,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for tests

    Each test gets a fresh session that is rolled back after the test

    Args:
        async_session_factory: Session factory

    Yields:
        AsyncSession instance
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def app(test_settings: Settings, async_engine: AsyncEngine):
    """
    Create FastAPI application for tests

    Args:
        test_settings: Test configuration
        async_engine: Database engine

    Returns:
        FastAPI application instance
    """
    from app.db.database import engine as prod_engine

    # Override settings
    def get_test_settings():
        return test_settings

    # Create app
    test_app = create_app()

    # Override dependencies
    test_app.dependency_overrides[get_settings] = get_test_settings

    # Override database session
    async def override_get_db():
        async_session_factory = sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    test_app.dependency_overrides[get_db] = override_get_db

    return test_app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP test client

    Args:
        app: FastAPI application

    Yields:
        AsyncClient instance
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_cookies() -> dict[str, str]:
    """
    Sample Google cookies for testing

    Returns:
        Dictionary of cookie name/value pairs
    """
    return {
        "SID": "test_sid_value_1234567890",
        "HSID": "test_hsid_value_1234567890",
        "SSID": "test_ssid_value_1234567890",
        "APISID": "test_apisid_value_1234567890",
        "SAPISID": "test_sapisid_value_1234567890",
        "__Secure-1PSID": "test_secure_1psid_value",
        "__Secure-3PSID": "test_secure_3psid_value",
    }


@pytest.fixture
def mock_course_data() -> dict[str, Any]:
    """
    Sample course data for testing

    Returns:
        Dictionary with course information
    """
    return {
        "id": "123456789",
        "name": "Test Course",
        "section": "Section A",
        "description": "Test course description",
        "state": "ACTIVE",
        "ownerId": "test_teacher@example.com",
        "creationTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-15T12:00:00Z",
        "courseGroupEmail": "test-course@example.com",
    }


@pytest.fixture
def mock_coursework_data() -> dict[str, Any]:
    """
    Sample coursework data for testing

    Returns:
        Dictionary with coursework information
    """
    return {
        "courseId": "123456789",
        "id": "987654321",
        "title": "Test Assignment",
        "description": "Test assignment with video",
        "state": "PUBLISHED",
        "workType": "ASSIGNMENT",
        "materials": [
            {
                "driveFile": {
                    "driveFile": {
                        "id": "video_file_id_123",
                        "title": "Test Video.mp4",
                        "alternateLink": "https://drive.google.com/file/d/video_file_id_123/view",
                    }
                }
            }
        ],
    }


@pytest.fixture
def temp_downloads_dir(tmp_path: Path) -> Path:
    """
    Temporary directory for download tests

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to downloads directory
    """
    downloads = tmp_path / "downloads"
    downloads.mkdir(exist_ok=True)
    return downloads


@pytest.fixture
def temp_secrets_dir(tmp_path: Path) -> Path:
    """
    Temporary directory for secrets (cookies, credentials)

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to secrets directory
    """
    secrets = tmp_path / ".secrets"
    secrets.mkdir(exist_ok=True)
    return secrets


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (database, HTTP)")
    config.addinivalue_line("markers", "slow: Slow tests (downloads, external APIs)")
    config.addinivalue_line("markers", "requires_docker: Tests requiring Docker")


# Auto-apply markers based on test location
def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test file location"""
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
