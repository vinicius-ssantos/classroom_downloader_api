"""
Google Classroom API service
"""
import logging
import re
from typing import Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GoogleClassroomService:
    """Service for interacting with Google Classroom API"""

    def __init__(self, credentials: Credentials):
        """
        Initialize with user credentials

        Args:
            credentials: Google OAuth2 Credentials
        """
        self.credentials = credentials
        self.classroom_service = build("classroom", "v1", credentials=credentials)
        self.drive_service = build("drive", "v3", credentials=credentials)

    async def list_courses(
        self,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List all courses for the authenticated user

        Args:
            page_size: Number of courses per page
            page_token: Page token for pagination

        Returns:
            Dictionary with courses and nextPageToken
        """
        try:
            params = {
                "pageSize": page_size,
            }
            if page_token:
                params["pageToken"] = page_token

            result = self.classroom_service.courses().list(**params).execute()

            return {
                "courses": result.get("courses", []),
                "nextPageToken": result.get("nextPageToken"),
            }

        except HttpError as e:
            logger.error(f"Failed to list courses: {e}")
            raise

    async def get_course(self, course_id: str) -> Optional[dict[str, Any]]:
        """
        Get a specific course by ID

        Args:
            course_id: Google Classroom course ID

        Returns:
            Course dictionary or None if not found
        """
        try:
            course = self.classroom_service.courses().get(id=course_id).execute()
            return course

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Course not found: {course_id}")
                return None
            logger.error(f"Failed to get course {course_id}: {e}")
            raise

    async def list_coursework(
        self,
        course_id: str,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List all coursework for a course

        Args:
            course_id: Google Classroom course ID
            page_size: Number of coursework items per page
            page_token: Page token for pagination

        Returns:
            Dictionary with coursework and nextPageToken
        """
        try:
            params = {
                "courseId": course_id,
                "pageSize": page_size,
            }
            if page_token:
                params["pageToken"] = page_token

            result = (
                self.classroom_service.courses()
                .courseWork()
                .list(**params)
                .execute()
            )

            return {
                "coursework": result.get("courseWork", []),
                "nextPageToken": result.get("nextPageToken"),
            }

        except HttpError as e:
            logger.error(f"Failed to list coursework for course {course_id}: {e}")
            raise

    async def list_course_materials(
        self,
        course_id: str,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List all course materials for a course

        Args:
            course_id: Google Classroom course ID
            page_size: Number of materials per page
            page_token: Page token for pagination

        Returns:
            Dictionary with materials and nextPageToken
        """
        try:
            params = {
                "courseId": course_id,
                "pageSize": page_size,
            }
            if page_token:
                params["pageToken"] = page_token

            result = (
                self.classroom_service.courses()
                .courseWorkMaterials()
                .list(**params)
                .execute()
            )

            return {
                "materials": result.get("courseWorkMaterial", []),
                "nextPageToken": result.get("nextPageToken"),
            }

        except HttpError as e:
            logger.error(f"Failed to list materials for course {course_id}: {e}")
            raise

    def extract_video_links(
        self,
        coursework_or_material: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extract video links from coursework or material

        Args:
            coursework_or_material: Coursework or material dictionary

        Returns:
            List of video link dictionaries with url, title, source_type
        """
        video_links = []

        # Check description for URLs
        description = coursework_or_material.get("description", "")
        if description:
            video_links.extend(self._extract_urls_from_text(description))

        # Check materials
        materials = coursework_or_material.get("materials", [])
        for material in materials:
            # YouTube video
            if "youtubeVideo" in material:
                youtube = material["youtubeVideo"]
                video_links.append({
                    "url": f"https://www.youtube.com/watch?v={youtube['id']}",
                    "title": youtube.get("title"),
                    "source_type": "youtube",
                    "video_id": youtube["id"],
                })

            # Google Drive file
            elif "driveFile" in material:
                drive_file = material["driveFile"]["driveFile"]
                file_id = drive_file["id"]
                mime_type = drive_file.get("mimeType", "")

                # Only process video files
                if mime_type.startswith("video/"):
                    video_links.append({
                        "url": f"https://drive.google.com/file/d/{file_id}/view",
                        "title": drive_file.get("title"),
                        "source_type": "drive",
                        "drive_file_id": file_id,
                        "drive_mime_type": mime_type,
                    })

            # Link with potential video
            elif "link" in material:
                link = material["link"]
                url = link.get("url", "")
                if self._is_video_url(url):
                    video_links.append({
                        "url": url,
                        "title": link.get("title"),
                        "source_type": self._detect_video_source(url),
                    })

        return video_links

    def _extract_urls_from_text(self, text: str) -> list[dict[str, Any]]:
        """
        Extract video URLs from text

        Args:
            text: Text to search for URLs

        Returns:
            List of video link dictionaries
        """
        video_links = []

        # URL regex pattern
        url_pattern = r"https?://[^\s<>\"']+"
        urls = re.findall(url_pattern, text)

        for url in urls:
            if self._is_video_url(url):
                video_links.append({
                    "url": url,
                    "title": None,
                    "source_type": self._detect_video_source(url),
                })

        return video_links

    def _is_video_url(self, url: str) -> bool:
        """
        Check if URL is likely a video

        Args:
            url: URL to check

        Returns:
            True if URL appears to be a video
        """
        video_domains = [
            "youtube.com",
            "youtu.be",
            "drive.google.com",
            "vimeo.com",
            "dailymotion.com",
            "wistia.com",
        ]

        url_lower = url.lower()
        return any(domain in url_lower for domain in video_domains)

    def _detect_video_source(self, url: str) -> str:
        """
        Detect video source from URL

        Args:
            url: Video URL

        Returns:
            Source type string
        """
        url_lower = url.lower()

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "drive.google.com" in url_lower:
            return "drive"
        elif "vimeo.com" in url_lower:
            return "vimeo"
        elif "dailymotion.com" in url_lower:
            return "dailymotion"
        elif "wistia.com" in url_lower:
            return "wistia"
        else:
            return "other"

    async def get_drive_file_info(self, file_id: str) -> Optional[dict[str, Any]]:
        """
        Get Google Drive file information

        Args:
            file_id: Google Drive file ID

        Returns:
            File information dictionary or None if not found
        """
        try:
            file_info = (
                self.drive_service.files()
                .get(fileId=file_id, fields="id,name,mimeType,size,webViewLink")
                .execute()
            )
            return file_info

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Drive file not found: {file_id}")
                return None
            logger.error(f"Failed to get drive file {file_id}: {e}")
            raise

    async def download_drive_video(self, file_id: str, output_path: str) -> bool:
        """
        Download video from Google Drive

        Args:
            file_id: Google Drive file ID
            output_path: Local path to save file

        Returns:
            True if download successful
        """
        try:
            request = self.drive_service.files().get_media(fileId=file_id)

            with open(output_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"Downloaded drive video {file_id} to {output_path}")
            return True

        except HttpError as e:
            logger.error(f"Failed to download drive video {file_id}: {e}")
            return False


def create_google_classroom_service(
    credentials: Credentials,
) -> GoogleClassroomService:
    """
    Factory function to create GoogleClassroomService

    Args:
        credentials: Google OAuth2 Credentials

    Returns:
        GoogleClassroomService instance
    """
    return GoogleClassroomService(credentials)
