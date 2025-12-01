"""
Downloads router for managing video download jobs
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db
from app.domain.models import DownloadStatus
from app.repositories.download_job_repository import DownloadJobRepository
from app.repositories.video_link_repository import VideoLinkRepository
from app.schemas.download import (
    DownloadBatchResponse,
    DownloadJobResponse,
    DownloadJobWithDetails,
    DownloadRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/downloads", tags=["downloads"])
settings = get_settings()


@router.post("", response_model=DownloadBatchResponse)
async def create_download_jobs(
    user_id: int = Query(..., description="User ID"),
    course_id: int = Query(..., description="Course ID"),
    request: DownloadRequest = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Create download jobs for video links

    Args:
        user_id: User ID
        course_id: Course ID
        request: Download request with video link IDs
        db: Database session

    Returns:
        Batch download response with created jobs
    """
    try:
        video_link_repo = VideoLinkRepository(db)
        download_job_repo = DownloadJobRepository(db)

        created_jobs = []
        failed_jobs = []

        for video_link_id in request.video_link_ids:
            try:
                # Verify video link exists
                video_link = await video_link_repo.get(video_link_id)
                if not video_link:
                    failed_jobs.append({
                        "video_link_id": str(video_link_id),
                        "error": "Video link not found",
                    })
                    continue

                # Create download job
                job = await download_job_repo.create(
                    user_id=user_id,
                    course_id=course_id,
                    video_link_id=video_link_id,
                    status=DownloadStatus.PENDING,
                )

                created_jobs.append(job)

            except Exception as e:
                logger.error(f"Failed to create job for video {video_link_id}: {e}")
                failed_jobs.append({
                    "video_link_id": str(video_link_id),
                    "error": str(e),
                })

        await db.commit()

        return DownloadBatchResponse(
            created_jobs=created_jobs,
            failed_jobs=failed_jobs,
            total_requested=len(request.video_link_ids),
            total_created=len(created_jobs),
            total_failed=len(failed_jobs),
        )

    except Exception as e:
        logger.error(f"Failed to create download jobs: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download jobs: {str(e)}",
        )


@router.get("", response_model=List[DownloadJobResponse])
async def list_download_jobs(
    user_id: int = Query(..., description="User ID"),
    course_id: int = Query(None, description="Filter by course ID"),
    status_filter: DownloadStatus = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    List download jobs

    Args:
        user_id: User ID
        course_id: Optional course ID filter
        status_filter: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records
        db: Database session

    Returns:
        List of download jobs
    """
    try:
        download_job_repo = DownloadJobRepository(db)

        if status_filter:
            jobs = await download_job_repo.get_by_status(status_filter, skip, limit)
        elif course_id:
            jobs = await download_job_repo.get_by_course(course_id, skip, limit)
        else:
            jobs = await download_job_repo.get_by_user(user_id, skip, limit)

        return jobs

    except Exception as e:
        logger.error(f"Failed to list download jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list download jobs",
        )


@router.get("/{job_id}", response_model=DownloadJobWithDetails)
async def get_download_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get download job with details

    Args:
        job_id: Download job ID
        db: Database session

    Returns:
        Download job with details
    """
    try:
        download_job_repo = DownloadJobRepository(db)
        job_data = await download_job_repo.get_with_details(job_id)

        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Download job not found",
            )

        # Construct response
        job = job_data["job"]
        return DownloadJobWithDetails(
            id=job.id,
            user_id=job.user_id,
            course_id=job.course_id,
            video_link_id=job.video_link_id,
            status=job.status,
            progress_percent=job.progress_percent,
            downloaded_bytes=job.downloaded_bytes,
            total_bytes=job.total_bytes,
            error_message=job.error_message,
            retry_count=job.retry_count,
            output_path=job.output_path,
            file_size_bytes=job.file_size_bytes,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
            video_url=job_data["video_url"],
            video_title=job_data["video_title"],
            course_name=job_data["course_name"],
            coursework_title=job_data["coursework_title"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get download job",
        )


@router.delete("/{job_id}")
async def cancel_download_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a download job

    Args:
        job_id: Download job ID
        db: Database session

    Returns:
        Success message
    """
    try:
        download_job_repo = DownloadJobRepository(db)
        job = await download_job_repo.get(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Download job not found",
            )

        # Only cancel if pending or downloading
        if job.status in (DownloadStatus.PENDING, DownloadStatus.DOWNLOADING):
            await download_job_repo.update_status(
                job_id,
                DownloadStatus.CANCELLED,
            )
            await db.commit()
            return {"success": True, "message": "Download job cancelled"}
        else:
            return {
                "success": False,
                "message": f"Cannot cancel job with status: {job.status.value}",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel download job: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel download job",
        )
