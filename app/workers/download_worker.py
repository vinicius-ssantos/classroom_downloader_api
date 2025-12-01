"""
Background worker for processing video download jobs
"""
import asyncio
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db_context
from app.domain.models import DownloadStatus
from app.repositories.download_job_repository import DownloadJobRepository
from app.repositories.video_link_repository import VideoLinkRepository
from app.services.video_downloader import DownloadProgress, get_video_downloader

logger = logging.getLogger(__name__)
settings = get_settings()


class DownloadWorker:
    """Worker for processing video download jobs"""

    def __init__(self):
        """Initialize download worker"""
        self.video_downloader = get_video_downloader()
        self.running = False
        self.current_jobs: set[int] = set()

    async def start(self):
        """
        Start the worker

        This method runs continuously, polling for pending jobs
        """
        self.running = True
        logger.info("Download worker started")

        while self.running:
            try:
                await self._process_pending_jobs()
                await asyncio.sleep(settings.worker_poll_interval_seconds)
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(settings.worker_poll_interval_seconds)

    async def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("Download worker stopped")

    async def _process_pending_jobs(self):
        """
        Process pending download jobs

        Fetches pending jobs and starts downloads up to max_concurrent_downloads
        """
        async with get_db_context() as db:
            download_job_repo = DownloadJobRepository(db)

            # Get pending jobs
            pending_jobs = await download_job_repo.get_by_status(
                DownloadStatus.PENDING,
                skip=0,
                limit=settings.max_concurrent_downloads,
            )

            # Filter out jobs already being processed
            jobs_to_process = [
                job for job in pending_jobs
                if job.id not in self.current_jobs
            ]

            # Calculate available slots
            available_slots = settings.max_concurrent_downloads - len(self.current_jobs)

            if available_slots <= 0:
                return

            # Process jobs up to available slots
            for job in jobs_to_process[:available_slots]:
                # Mark as being processed
                self.current_jobs.add(job.id)

                # Start download in background
                asyncio.create_task(self._process_download_job(job.id))

                logger.info(f"Started processing download job {job.id}")

    async def _process_download_job(self, job_id: int):
        """
        Process a single download job

        Args:
            job_id: Download job ID
        """
        try:
            async with get_db_context() as db:
                download_job_repo = DownloadJobRepository(db)
                video_link_repo = VideoLinkRepository(db)

                # Get job details
                job_data = await download_job_repo.get_with_details(job_id)

                if not job_data:
                    logger.error(f"Job {job_id} not found")
                    return

                job = job_data["job"]
                video_url = job_data["video_url"]
                course_name = job_data["course_name"]

                # Update status to downloading
                await download_job_repo.update_status(
                    job_id,
                    DownloadStatus.DOWNLOADING,
                )
                await db.commit()

                logger.info(f"Downloading video from: {video_url}")

                # Create subdirectory for course
                course_subdir = self._sanitize_filename(course_name)

                # Progress callback
                async def progress_callback(progress: DownloadProgress):
                    """Update job progress in database"""
                    try:
                        async with get_db_context() as progress_db:
                            progress_repo = DownloadJobRepository(progress_db)
                            await progress_repo.update_progress(
                                job_id,
                                progress.progress_percent,
                                progress.downloaded_bytes,
                                progress.total_bytes,
                            )
                            await progress_db.commit()
                    except Exception as e:
                        logger.error(f"Failed to update progress: {e}")

                # Download video
                success, output_path, error_message = await self.video_downloader.download_video(
                    url=video_url,
                    output_subdir=course_subdir,
                    progress_callback=progress_callback,
                )

                # Update job status
                if success and output_path:
                    # Mark job as completed
                    await download_job_repo.update(
                        job_id,
                        status=DownloadStatus.COMPLETED,
                        progress_percent=100,
                        output_path=str(output_path),
                        file_size_bytes=output_path.stat().st_size,
                    )

                    # Mark video link as downloaded
                    await video_link_repo.mark_as_downloaded(
                        job.video_link_id,
                        str(output_path),
                        output_path.stat().st_size,
                    )

                    await db.commit()
                    logger.info(f"Successfully completed download job {job_id}")

                else:
                    # Check if should retry
                    if job.retry_count < settings.worker_max_retries:
                        # Increment retry and reset to pending
                        await download_job_repo.increment_retry_count(job_id)
                        await download_job_repo.update_status(
                            job_id,
                            DownloadStatus.PENDING,
                            error_message=error_message,
                        )
                        await db.commit()
                        logger.warning(
                            f"Download job {job_id} failed, retry {job.retry_count + 1}/{settings.worker_max_retries}"
                        )
                    else:
                        # Mark as failed
                        await download_job_repo.update_status(
                            job_id,
                            DownloadStatus.FAILED,
                            error_message=error_message,
                        )
                        await db.commit()
                        logger.error(f"Download job {job_id} failed after max retries")

        except Exception as e:
            logger.error(f"Error processing download job {job_id}: {e}", exc_info=True)

            # Mark job as failed
            try:
                async with get_db_context() as db:
                    download_job_repo = DownloadJobRepository(db)
                    await download_job_repo.update_status(
                        job_id,
                        DownloadStatus.FAILED,
                        error_message=str(e),
                    )
                    await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")

        finally:
            # Remove from current jobs
            self.current_jobs.discard(job_id)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe filesystem usage

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Limit length
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length]

        return filename


# Global worker instance
_worker: DownloadWorker | None = None


def get_download_worker() -> DownloadWorker:
    """
    Get singleton download worker instance

    Returns:
        DownloadWorker instance
    """
    global _worker
    if _worker is None:
        _worker = DownloadWorker()
    return _worker
