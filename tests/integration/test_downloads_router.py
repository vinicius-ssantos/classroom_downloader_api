"""
Integration tests for downloads endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    Course,
    Coursework,
    DownloadJob,
    DownloadStatus,
    User,
    VideoLink,
)
from app.repositories.course_repository import CourseRepository
from app.repositories.coursework_repository import CourseworkRepository
from app.repositories.download_job_repository import DownloadJobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.video_link_repository import VideoLinkRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_downloads_empty(client: AsyncClient):
    """Test listing downloads when no downloads exist"""
    response = await client.get("/downloads?user_id=1")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_download_job(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test creating a download job"""
    # Create test data
    user_repo = UserRepository(db_session)
    user = User(email="test@example.com", google_id="test_google_id")
    await user_repo.add(user)

    course_repo = CourseRepository(db_session)
    course = Course(
        google_course_id="course_123",
        name="Test Course",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course)

    coursework_repo = CourseworkRepository(db_session)
    coursework = Coursework(
        course_id=course.id,
        google_coursework_id="coursework_123",
        title="Test Assignment",
        state="PUBLISHED",
        work_type="ASSIGNMENT",
    )
    await coursework_repo.add(coursework)

    video_link_repo = VideoLinkRepository(db_session)
    video_link = VideoLink(
        coursework_id=coursework.id,
        url="https://drive.google.com/file/d/test_video_id/view",
        source_type="google_drive",
        drive_file_id="test_video_id",
    )
    await video_link_repo.add(video_link)
    await db_session.commit()

    # Test endpoint
    response = await client.post(
        f"/downloads?user_id={user.id}&course_id={course.id}",
        json={"video_link_ids": [video_link.id]},
    )

    assert response.status_code == 200
    data = response.json()
    assert "jobs_created" in data
    assert data["jobs_created"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_download_job_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test getting download job details"""
    # Create test data
    user_repo = UserRepository(db_session)
    user = User(email="test@example.com", google_id="test_google_id")
    await user_repo.add(user)

    course_repo = CourseRepository(db_session)
    course = Course(
        google_course_id="course_123",
        name="Test Course",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course)

    coursework_repo = CourseworkRepository(db_session)
    coursework = Coursework(
        course_id=course.id,
        google_coursework_id="coursework_123",
        title="Test Assignment",
        state="PUBLISHED",
        work_type="ASSIGNMENT",
    )
    await coursework_repo.add(coursework)

    video_link_repo = VideoLinkRepository(db_session)
    video_link = VideoLink(
        coursework_id=coursework.id,
        url="https://drive.google.com/file/d/test_video_id/view",
        source_type="google_drive",
        drive_file_id="test_video_id",
    )
    await video_link_repo.add(video_link)

    download_repo = DownloadJobRepository(db_session)
    job = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.PENDING,
        progress_percent=0.0,
    )
    await download_repo.add(job)
    await db_session.commit()

    # Test endpoint
    response = await client.get(f"/downloads/{job.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["status"] == "PENDING"
    assert data["progress_percent"] == 0.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_download_job_not_found(client: AsyncClient):
    """Test getting non-existent download job returns 404"""
    response = await client.get("/downloads/999")

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_download_job(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test cancelling a download job"""
    # Create test data
    user_repo = UserRepository(db_session)
    user = User(email="test@example.com", google_id="test_google_id")
    await user_repo.add(user)

    course_repo = CourseRepository(db_session)
    course = Course(
        google_course_id="course_123",
        name="Test Course",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course)

    coursework_repo = CourseworkRepository(db_session)
    coursework = Coursework(
        course_id=course.id,
        google_coursework_id="coursework_123",
        title="Test Assignment",
        state="PUBLISHED",
        work_type="ASSIGNMENT",
    )
    await coursework_repo.add(coursework)

    video_link_repo = VideoLinkRepository(db_session)
    video_link = VideoLink(
        coursework_id=coursework.id,
        url="https://drive.google.com/file/d/test_video_id/view",
        source_type="google_drive",
        drive_file_id="test_video_id",
    )
    await video_link_repo.add(video_link)

    download_repo = DownloadJobRepository(db_session)
    job = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.PENDING,
        progress_percent=0.0,
    )
    await download_repo.add(job)
    await db_session.commit()

    # Test endpoint
    response = await client.delete(f"/downloads/{job.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["status"] == "CANCELLED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_downloads_with_filters(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test listing downloads with filters"""
    # Create test data
    user_repo = UserRepository(db_session)
    user = User(email="test@example.com", google_id="test_google_id")
    await user_repo.add(user)

    course_repo = CourseRepository(db_session)
    course = Course(
        google_course_id="course_123",
        name="Test Course",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course)

    coursework_repo = CourseworkRepository(db_session)
    coursework = Coursework(
        course_id=course.id,
        google_coursework_id="coursework_123",
        title="Test Assignment",
        state="PUBLISHED",
        work_type="ASSIGNMENT",
    )
    await coursework_repo.add(coursework)

    video_link_repo = VideoLinkRepository(db_session)
    video_link = VideoLink(
        coursework_id=coursework.id,
        url="https://drive.google.com/file/d/test_video_id/view",
        source_type="google_drive",
        drive_file_id="test_video_id",
    )
    await video_link_repo.add(video_link)

    download_repo = DownloadJobRepository(db_session)
    job1 = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.PENDING,
        progress_percent=0.0,
    )
    job2 = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.COMPLETED,
        progress_percent=100.0,
    )
    await download_repo.add(job1)
    await download_repo.add(job2)
    await db_session.commit()

    # Test endpoint with user filter
    response = await client.get(f"/downloads?user_id={user.id}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
