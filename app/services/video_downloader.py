"""
Video downloader service using yt-dlp
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional

import yt_dlp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DownloadProgress:
    """Progress tracker for video downloads"""

    def __init__(self):
        self.downloaded_bytes: int = 0
        self.total_bytes: Optional[int] = None
        self.progress_percent: int = 0
        self.status: str = "pending"
        self.filename: Optional[str] = None
        self.error: Optional[str] = None


class VideoDownloaderService:
    """Service for downloading videos using yt-dlp"""

    def __init__(self):
        self.download_dir = settings.download_path
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _get_yt_dlp_options(
        self,
        output_path: Path,
        progress_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> dict[str, Any]:
        """
        Get yt-dlp options configuration

        Args:
            output_path: Output directory for downloads
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary of yt-dlp options
        """
        options = {
            "format": settings.ytdlp_format,
            "outtmpl": str(output_path / settings.ytdlp_output_template),
            "quiet": False,
            "no_warnings": False,
            "extract_flat": False,
            "nocheckcertificate": False,
            "ignoreerrors": False,
            "retries": settings.worker_max_retries,
            "fragment_retries": settings.worker_max_retries,
            "socket_timeout": 30,
            "http_chunk_size": 10485760,  # 10MB
            # Output options
            "writeinfojson": False,
            "writethumbnail": False,
            "writedescription": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            # Post-processing
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
        }

        if progress_callback:
            options["progress_hooks"] = [progress_callback]

        return options

    def _progress_hook(self, d: dict[str, Any], progress: DownloadProgress) -> None:
        """
        yt-dlp progress hook

        Args:
            d: Progress dictionary from yt-dlp
            progress: DownloadProgress object to update
        """
        if d["status"] == "downloading":
            progress.status = "downloading"
            progress.downloaded_bytes = d.get("downloaded_bytes", 0)
            progress.total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")

            if progress.total_bytes:
                progress.progress_percent = int(
                    (progress.downloaded_bytes / progress.total_bytes) * 100
                )

            progress.filename = d.get("filename")
            logger.debug(
                f"Download progress: {progress.progress_percent}% "
                f"({progress.downloaded_bytes}/{progress.total_bytes} bytes)"
            )

        elif d["status"] == "finished":
            progress.status = "finished"
            progress.progress_percent = 100
            progress.filename = d.get("filename")
            logger.info(f"Download finished: {progress.filename}")

        elif d["status"] == "error":
            progress.status = "error"
            progress.error = str(d.get("error", "Unknown error"))
            logger.error(f"Download error: {progress.error}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(yt_dlp.utils.DownloadError),
    )
    async def download_video(
        self,
        url: str,
        output_subdir: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> tuple[bool, Optional[Path], Optional[str]]:
        """
        Download a video from URL

        Args:
            url: Video URL to download
            output_subdir: Optional subdirectory for output
            progress_callback: Optional callback function for progress updates

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            # Prepare output directory
            output_path = self.download_dir
            if output_subdir:
                output_path = output_path / output_subdir
                output_path.mkdir(parents=True, exist_ok=True)

            # Setup progress tracking
            progress = DownloadProgress()

            def yt_dlp_hook(d: dict[str, Any]) -> None:
                self._progress_hook(d, progress)
                if progress_callback:
                    progress_callback(progress)

            # Get yt-dlp options
            ydl_opts = self._get_yt_dlp_options(output_path, yt_dlp_hook)

            # Download video in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._download_sync,
                url,
                ydl_opts,
            )

            # Check if download was successful
            if progress.status == "error" or not progress.filename:
                error_msg = progress.error or "Download failed - no output file"
                logger.error(f"Download failed for {url}: {error_msg}")
                return False, None, error_msg

            output_file = Path(progress.filename)
            if not output_file.exists():
                error_msg = f"Output file not found: {output_file}"
                logger.error(error_msg)
                return False, None, error_msg

            logger.info(f"Successfully downloaded: {url} -> {output_file}")
            return True, output_file, None

        except yt_dlp.utils.DownloadError as e:
            error_msg = f"yt-dlp download error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error during download: {str(e)}"
            logger.exception(error_msg)
            return False, None, error_msg

    def _download_sync(self, url: str, ydl_opts: dict[str, Any]) -> None:
        """
        Synchronous download function to run in thread pool

        Args:
            url: Video URL
            ydl_opts: yt-dlp options
        """
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    async def get_video_info(self, url: str) -> Optional[dict[str, Any]]:
        """
        Extract video information without downloading

        Args:
            url: Video URL

        Returns:
            Video information dictionary or None if failed
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
            }

            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_sync,
                url,
                ydl_opts,
            )

            return info

        except Exception as e:
            logger.error(f"Failed to extract video info for {url}: {e}")
            return None

    def _extract_info_sync(self, url: str, ydl_opts: dict[str, Any]) -> dict[str, Any]:
        """
        Synchronous info extraction to run in thread pool

        Args:
            url: Video URL
            ydl_opts: yt-dlp options

        Returns:
            Video information dictionary
        """
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def is_supported_url(self, url: str) -> bool:
        """
        Check if URL is supported by yt-dlp

        Args:
            url: Video URL

        Returns:
            True if URL is supported
        """
        try:
            extractors = yt_dlp.extractor.gen_extractors()
            for extractor in extractors:
                if extractor.suitable(url):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking URL support: {e}")
            return False


# Singleton instance
_video_downloader: Optional[VideoDownloaderService] = None


def get_video_downloader() -> VideoDownloaderService:
    """
    Get singleton video downloader service instance

    Returns:
        VideoDownloaderService instance
    """
    global _video_downloader
    if _video_downloader is None:
        _video_downloader = VideoDownloaderService()
    return _video_downloader
