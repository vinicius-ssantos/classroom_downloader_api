"""
Courses router for managing Google Classroom courses
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_user_credentials
from app.core.config import get_settings
from app.db import get_db
from app.repositories.course_repository import CourseRepository
from app.repositories.coursework_repository import CourseworkRepository
from app.repositories.video_link_repository import VideoLinkRepository
from app.schemas.course import CourseResponse, CourseSummary
from app.schemas.coursework import CourseworkWithVideos
from app.services.google_classroom import create_google_classroom_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["courses"])
settings = get_settings()


@router.get("", response_model=List[CourseSummary])
async def list_courses(
    user_id: int = Query(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    List all courses for a user with summary statistics

    Args:
        user_id: User ID
        skip: Number of records to skip
        limit: Maximum number of records
        db: Database session

    Returns:
        List of course summaries
    """
    try:
        course_repo = CourseRepository(db)
        summaries = await course_repo.get_summary(user_id)
        return summaries[skip:skip + limit]

    except Exception as e:
        logger.error(f"Failed to list courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list courses",
        )


@router.post("/sync")
async def sync_courses(
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Sync courses from Google Classroom

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Sync result
    """
    try:
        # Get user credentials
        credentials = await get_user_credentials(user_id, db)

        # Create Google Classroom service
        classroom_service = create_google_classroom_service(credentials)

        # List courses from Google
        result = await classroom_service.list_courses()
        courses = result.get("courses", [])

        # Save to database
        course_repo = CourseRepository(db)
        synced_count = 0

        for course_data in courses:
            google_course_id = course_data["id"]

            # Check if course exists
            existing = await course_repo.get_by_google_course_id(google_course_id)

            if existing:
                # Update existing course
                await course_repo.update(
                    existing.id,
                    name=course_data.get("name", ""),
                    section=course_data.get("section"),
                    description=course_data.get("description"),
                    room=course_data.get("room"),
                    state=course_data.get("courseState", "UNKNOWN"),
                    alternate_link=course_data.get("alternateLink"),
                )
                await course_repo.update_last_synced(existing.id)
            else:
                # Create new course
                await course_repo.create(
                    google_course_id=google_course_id,
                    name=course_data.get("name", ""),
                    section=course_data.get("section"),
                    description=course_data.get("description"),
                    room=course_data.get("room"),
                    state=course_data.get("courseState", "UNKNOWN"),
                    alternate_link=course_data.get("alternateLink"),
                    owner_id=user_id,
                )

            synced_count += 1

        await db.commit()

        return {
            "success": True,
            "synced_count": synced_count,
            "total_courses": len(courses),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync courses: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync courses: {str(e)}",
        )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific course

    Args:
        course_id: Course ID
        db: Database session

    Returns:
        Course details
    """
    try:
        course_repo = CourseRepository(db)
        course = await course_repo.get(course_id)

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        return course

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course",
        )


@router.post("/{course_id}/sync-coursework")
async def sync_coursework(
    course_id: int,
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Sync coursework and extract video links for a course

    Args:
        course_id: Course ID
        user_id: User ID
        db: Database session

    Returns:
        Sync result with video count
    """
    try:
        # Get course
        course_repo = CourseRepository(db)
        course = await course_repo.get(course_id)

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        # Get credentials
        credentials = await get_user_credentials(user_id, db)
        classroom_service = create_google_classroom_service(credentials)

        # Fetch coursework
        coursework_result = await classroom_service.list_coursework(
            course.google_course_id
        )
        coursework_list = coursework_result.get("coursework", [])

        # Fetch materials
        materials_result = await classroom_service.list_course_materials(
            course.google_course_id
        )
        materials_list = materials_result.get("materials", [])

        # Combine both
        all_items = coursework_list + materials_list

        coursework_repo = CourseworkRepository(db)
        video_link_repo = VideoLinkRepository(db)
        synced_count = 0
        video_count = 0

        for item in all_items:
            google_coursework_id = item["id"]

            # Check if exists
            existing = await coursework_repo.get_by_google_coursework_id(
                google_coursework_id
            )

            if not existing:
                # Create coursework
                work_type = item.get("workType", "MATERIAL")
                existing = await coursework_repo.create(
                    google_coursework_id=google_coursework_id,
                    course_id=course.id,
                    title=item.get("title", "Untitled"),
                    description=item.get("description"),
                    work_type=work_type,
                    state=item.get("state", "PUBLISHED"),
                    alternate_link=item.get("alternateLink"),
                )

            synced_count += 1

            # Extract and save video links
            video_links = classroom_service.extract_video_links(item)

            for video_data in video_links:
                # Check if video link exists
                existing_video = await video_link_repo.get_by_url(video_data["url"])

                if not existing_video:
                    await video_link_repo.create(
                        coursework_id=existing.id,
                        url=video_data["url"],
                        title=video_data.get("title"),
                        source_type=video_data["source_type"],
                        drive_file_id=video_data.get("drive_file_id"),
                        drive_mime_type=video_data.get("drive_mime_type"),
                    )
                    video_count += 1

        await db.commit()

        return {
            "success": True,
            "synced_coursework": synced_count,
            "new_videos": video_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync coursework: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync coursework: {str(e)}",
        )


@router.get("/{course_id}/coursework", response_model=List[CourseworkWithVideos])
async def list_coursework(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    List all coursework with video links for a course

    Args:
        course_id: Course ID
        db: Database session

    Returns:
        List of coursework with videos
    """
    try:
        coursework_repo = CourseworkRepository(db)
        coursework_list = await coursework_repo.get_all_with_videos_by_course(course_id)

        return coursework_list

    except Exception as e:
        logger.error(f"Failed to list coursework: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list coursework",
        )
