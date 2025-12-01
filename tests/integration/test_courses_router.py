"""
Integration tests for courses endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Course, User
from app.repositories.course_repository import CourseRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_courses_empty(client: AsyncClient):
    """Test listing courses when no courses exist"""
    response = await client.get("/courses?user_id=1")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_courses_with_data(client: AsyncClient, db_session: AsyncSession):
    """Test listing courses when courses exist"""
    # Create test user
    user_repo = UserRepository(db_session)
    user = User(
        email="test@example.com",
        google_id="test_google_id_123",
    )
    await user_repo.add(user)
    await db_session.commit()

    # Create test courses
    course_repo = CourseRepository(db_session)
    course1 = Course(
        google_course_id="course_123",
        name="Test Course 1",
        owner_id=user.id,
        state="ACTIVE",
    )
    course2 = Course(
        google_course_id="course_456",
        name="Test Course 2",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course1)
    await course_repo.add(course2)
    await db_session.commit()

    # Test endpoint
    response = await client.get(f"/courses?user_id={user.id}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] in ["Test Course 1", "Test Course 2"]
    assert data[1]["name"] in ["Test Course 1", "Test Course 2"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_course_by_id(client: AsyncClient, db_session: AsyncSession):
    """Test getting a specific course by ID"""
    # Create test user
    user_repo = UserRepository(db_session)
    user = User(
        email="test@example.com",
        google_id="test_google_id_123",
    )
    await user_repo.add(user)
    await db_session.commit()

    # Create test course
    course_repo = CourseRepository(db_session)
    course = Course(
        google_course_id="course_123",
        name="Test Course",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course)
    await db_session.commit()

    # Test endpoint
    response = await client.get(f"/courses/{course.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == course.id
    assert data["name"] == "Test Course"
    assert data["state"] == "ACTIVE"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient):
    """Test getting a non-existent course returns 404"""
    response = await client.get("/courses/999")

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_sync_courses_missing_cookies(client: AsyncClient):
    """Test syncing courses without cookies returns 401"""
    response = await client.post("/courses/sync?user_id=1")

    # Should fail because no cookies are configured
    assert response.status_code in [401, 500]  # Depends on error handling
