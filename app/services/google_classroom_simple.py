"""
Google Classroom service usando apenas cookies (sem OAuth2)
"""
import logging
import re
from typing import Any, Optional

from app.services.http_client import get_http_client

logger = logging.getLogger(__name__)


class GoogleClassroomSimpleService:
    """
    Serviço simplificado do Google Classroom usando apenas cookies
    Não precisa de OAuth2!
    """

    def __init__(self):
        """Initialize service"""
        self.http_client = get_http_client()
        self.base_url = "https://classroom.googleapis.com/v1"

    async def list_courses(self, page_token: Optional[str] = None) -> dict[str, Any]:
        """
        Lista todos os cursos do usuário

        Args:
            page_token: Token para paginação

        Returns:
            Dict com courses e nextPageToken
        """
        try:
            params = {"pageSize": 50}
            if page_token:
                params["pageToken"] = page_token

            response = await self.http_client.get(
                f"{self.base_url}/courses",
                params=params,
            )

            data = response.json()
            return {
                "courses": data.get("courses", []),
                "nextPageToken": data.get("nextPageToken"),
            }

        except Exception as e:
            logger.error(f"Erro ao listar cursos: {e}")
            raise

    async def get_course(self, course_id: str) -> Optional[dict[str, Any]]:
        """
        Busca um curso específico

        Args:
            course_id: ID do curso

        Returns:
            Dados do curso ou None
        """
        try:
            response = await self.http_client.get(
                f"{self.base_url}/courses/{course_id}"
            )
            return response.json()

        except Exception as e:
            logger.error(f"Erro ao buscar curso {course_id}: {e}")
            return None

    async def list_coursework(
        self,
        course_id: str,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Lista materiais/atividades de um curso

        Args:
            course_id: ID do curso
            page_token: Token para paginação

        Returns:
            Dict com coursework e nextPageToken
        """
        try:
            params = {"pageSize": 50}
            if page_token:
                params["pageToken"] = page_token

            response = await self.http_client.get(
                f"{self.base_url}/courses/{course_id}/courseWork",
                params=params,
            )

            data = response.json()
            return {
                "coursework": data.get("courseWork", []),
                "nextPageToken": data.get("nextPageToken"),
            }

        except Exception as e:
            logger.error(f"Erro ao listar coursework do curso {course_id}: {e}")
            raise

    async def list_course_materials(
        self,
        course_id: str,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Lista materiais do curso

        Args:
            course_id: ID do curso
            page_token: Token para paginação

        Returns:
            Dict com materials e nextPageToken
        """
        try:
            params = {"pageSize": 50}
            if page_token:
                params["pageToken"] = page_token

            response = await self.http_client.get(
                f"{self.base_url}/courses/{course_id}/courseWorkMaterials",
                params=params,
            )

            data = response.json()
            return {
                "materials": data.get("courseWorkMaterial", []),
                "nextPageToken": data.get("nextPageToken"),
            }

        except Exception as e:
            logger.error(f"Erro ao listar materiais do curso {course_id}: {e}")
            raise

    def extract_video_links(
        self,
        coursework_or_material: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extrai links de vídeos de materiais/atividades

        Args:
            coursework_or_material: Dados do material

        Returns:
            Lista de dicts com info dos vídeos
        """
        video_links = []

        # Verificar descrição
        description = coursework_or_material.get("description", "")
        if description:
            video_links.extend(self._extract_urls_from_text(description))

        # Verificar materiais anexos
        materials = coursework_or_material.get("materials", [])
        for material in materials:
            # YouTube
            if "youtubeVideo" in material:
                youtube = material["youtubeVideo"]
                video_links.append({
                    "url": f"https://www.youtube.com/watch?v={youtube['id']}",
                    "title": youtube.get("title"),
                    "source_type": "youtube",
                    "video_id": youtube["id"],
                })

            # Google Drive
            elif "driveFile" in material:
                drive_file = material["driveFile"]["driveFile"]
                file_id = drive_file["id"]
                mime_type = drive_file.get("mimeType", "")

                if mime_type.startswith("video/"):
                    video_links.append({
                        "url": f"https://drive.google.com/file/d/{file_id}/view",
                        "title": drive_file.get("title"),
                        "source_type": "drive",
                        "drive_file_id": file_id,
                        "drive_mime_type": mime_type,
                    })

            # Link genérico
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
        """Extrai URLs de vídeo do texto"""
        video_links = []
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
        """Verifica se URL é de vídeo"""
        video_domains = [
            "youtube.com", "youtu.be",
            "drive.google.com",
            "vimeo.com",
            "dailymotion.com",
        ]
        return any(domain in url.lower() for domain in video_domains)

    def _detect_video_source(self, url: str) -> str:
        """Detecta a fonte do vídeo pela URL"""
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "drive.google.com" in url_lower:
            return "drive"
        elif "vimeo.com" in url_lower:
            return "vimeo"
        else:
            return "other"


def create_classroom_service() -> GoogleClassroomSimpleService:
    """
    Factory para criar serviço do Classroom

    Returns:
        GoogleClassroomSimpleService instance
    """
    return GoogleClassroomSimpleService()
