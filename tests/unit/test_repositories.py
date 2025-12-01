"""
Unit tests for repository layer
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    Course,
    DownloadJob,
    DownloadStatus,
    User,
    VideoLink,
    Coursework,
)
from app.repositories.course_repository import CourseRepository
from app.repositories.download_job_repository import DownloadJobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.video_link_repository import VideoLinkRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_add(db_session: AsyncSession):
    """Test adding a user to the database"""
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        google_id="test_google_id_123",
    )

    result = await repo.add(user)
    await db_session.commit()

    assert result.id is not None
    assert result.email == "test@example.com"
    assert result.google_id == "test_google_id_123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_get(db_session: AsyncSession):
    """Test getting a user by ID"""
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        google_id="test_google_id_123",
    )
    await repo.add(user)
    await db_session.commit()

    result = await repo.get(user.id)

    assert result is not None
    assert result.id == user.id
    assert result.email == "test@example.com"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_get_nonexistent(db_session: AsyncSession):
    """Test getting a non-existent user returns None"""
    repo = UserRepository(db_session)

    result = await repo.get(999)

    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_course_repository_add(db_session: AsyncSession):
    """Test adding a course to the database"""
    # Create user first
    user_repo = UserRepository(db_session)
    user = User(email="test@example.com", google_id="test_google_id")
    await user_repo.add(user)
    await db_session.commit()

    # Add course
    course_repo = CourseRepository(db_session)
    course = Course(
        google_course_id="course_123",
        name="Test Course",
        owner_id=user.id,
        state="ACTIVE",
    )

    result = await course_repo.add(course)
    await db_session.commit()

    assert result.id is not None
    assert result.name == "Test Course"
    assert result.google_course_id == "course_123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_course_repository_get_by_user(db_session: AsyncSession):
    """Test getting courses by user ID"""
    # Create user
    user_repo = UserRepository(db_session)
    user = User(email="test@example.com", google_id="test_google_id")
    await user_repo.add(user)

    # Add courses
    course_repo = CourseRepository(db_session)
    course1 = Course(
        google_course_id="course_123",
        name="Course 1",
        owner_id=user.id,
        state="ACTIVE",
    )
    course2 = Course(
        google_course_id="course_456",
        name="Course 2",
        owner_id=user.id,
        state="ACTIVE",
    )
    await course_repo.add(course1)
    await course_repo.add(course2)
    await db_session.commit()

    # Query
    results = await course_repo.get_by_user(user.id)

    assert len(results) == 2
    assert all(c.owner_id == user.id for c in results)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_job_repository_get_by_status(db_session: AsyncSession):
    """Test getting download jobs by status"""
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

    coursework_repo = app.repositories.coursework_repository.CourseworkRepository(
        db_session
    )
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
        url="https://drive.google.com/file/d/test/view",
        source_type="google_drive",
        drive_file_id="test",
    )
    await video_link_repo.add(video_link)

    # Create jobs with different statuses
    job_repo = DownloadJobRepository(db_session)
    job1 = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.PENDING,
    )
    job2 = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.PENDING,
    )
    job3 = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.COMPLETED,
    )
    await job_repo.add(job1)
    await job_repo.add(job2)
    await job_repo.add(job3)
    await db_session.commit()

    # Query pending jobs
    pending = await job_repo.get_by_status(DownloadStatus.PENDING, limit=10)

    assert len(pending) == 2
    assert all(j.status == DownloadStatus.PENDING for j in pending)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_job_repository_update_status(db_session: AsyncSession):
    """Test updating download job status"""
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

    coursework_repo = app.repositories.coursework_repository.CourseworkRepository(
        db_session
    )
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
        url="https://drive.google.com/file/d/test/view",
        source_type="google_drive",
        drive_file_id="test",
    )
    await video_link_repo.add(video_link)

    job_repo = DownloadJobRepository(db_session)
    job = DownloadJob(
        user_id=user.id,
        course_id=course.id,
        video_link_id=video_link.id,
        status=DownloadStatus.PENDING,
    )
    await job_repo.add(job)
    await db_session.commit()

    # Update status
    job.status = DownloadStatus.DOWNLOADING
    await job_repo.update(job)
    await db_session.commit()

    # Verify
    updated = await job_repo.get(job.id)
    assert updated.status == DownloadStatus.DOWNLOADING


@pytest.mark.unit
@pytest.mark.asyncio
async def test_video_link_repository_get_by_coursework(db_session: AsyncSession):
    """Test getting video links by coursework ID"""
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

    coursework_repo = app.repositories.coursework_repository.CourseworkRepository(
        db_session
    )
    coursework = Coursework(
        course_id=course.id,
        google_coursework_id="coursework_123",
        title="Test Assignment",
        state="PUBLISHED",
        work_type="ASSIGNMENT",
    )
    await coursework_repo.add(coursework)

    # Add video links
    video_link_repo = VideoLinkRepository(db_session)
    link1 = VideoLink(
        coursework_id=coursework.id,
        url="https://drive.google.com/file/d/test1/view",
        source_type="google_drive",
        drive_file_id="test1",
    )
    link2 = VideoLink(
        coursework_id=coursework.id,
        url="https://drive.google.com/file/d/test2/view",
        source_type="google_drive",
        drive_file_id="test2",
    )
    await video_link_repo.add(link1)
    await video_link_repo.add(link2)
    await db_session.commit()

    # Query
    results = await video_link_repo.get_by_coursework(coursework.id)

    assert len(results) == 2
    assert all(v.coursework_id == coursework.id for v in results)
