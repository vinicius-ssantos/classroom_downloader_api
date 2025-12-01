"""
Courses router simplificado - usa apenas cookies, sem OAuth2!
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.repositories.course_repository import CourseRepository
from app.repositories.coursework_repository import CourseworkRepository
from app.repositories.video_link_repository import VideoLinkRepository
from app.schemas.course import CourseSummary
from app.schemas.coursework import CourseworkWithVideos
from app.services.cookie_manager import get_cookie_manager
from app.services.google_classroom_simple import create_classroom_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["courses"])


def check_cookies():
    """Dependency para verificar se cookies existem"""
    cookie_manager = get_cookie_manager()
    if not cookie_manager.has_cookies():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cookies não encontrados! Execute: python import_cookies.py",
        )


@router.get("", response_model=List[CourseSummary], dependencies=[Depends(check_cookies)])
async def list_courses(
    user_id: int = Query(1, description="User ID (sempre 1 sem OAuth2)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todos os cursos com estatísticas

    **Nota:** Sem OAuth2, sempre use user_id=1
    """
    try:
        course_repo = CourseRepository(db)
        summaries = await course_repo.get_summary(user_id)
        return summaries[skip:skip + limit]

    except Exception as e:
        logger.error(f"Erro ao listar cursos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar cursos: {str(e)}",
        )


@router.post("/sync", dependencies=[Depends(check_cookies)])
async def sync_courses(
    user_id: int = Query(1, description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Sincroniza cursos do Google Classroom

    Busca todos os cursos e salva no banco local
    """
    try:
        # Criar serviço do Classroom
        classroom_service = create_classroom_service()

        # Buscar cursos
        result = await classroom_service.list_courses()
        courses = result.get("courses", [])

        # Salvar no banco
        course_repo = CourseRepository(db)
        synced_count = 0

        for course_data in courses:
            google_course_id = course_data["id"]

            # Verificar se já existe
            existing = await course_repo.get_by_google_course_id(google_course_id)

            if existing:
                # Atualizar
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
                # Criar novo
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
        logger.error(f"Erro ao sincronizar cursos: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sincronizar cursos: {str(e)}",
        )


@router.post("/{course_id}/sync-coursework", dependencies=[Depends(check_cookies)])
async def sync_coursework(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Sincroniza materiais de um curso e extrai vídeos
    """
    try:
        # Buscar curso
        course_repo = CourseRepository(db)
        course = await course_repo.get(course_id)

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curso não encontrado",
            )

        # Criar serviço
        classroom_service = create_classroom_service()

        # Buscar coursework
        coursework_result = await classroom_service.list_coursework(
            course.google_course_id
        )
        coursework_list = coursework_result.get("coursework", [])

        # Buscar materiais
        materials_result = await classroom_service.list_course_materials(
            course.google_course_id
        )
        materials_list = materials_result.get("materials", [])

        # Combinar
        all_items = coursework_list + materials_list

        coursework_repo = CourseworkRepository(db)
        video_link_repo = VideoLinkRepository(db)
        synced_count = 0
        video_count = 0

        for item in all_items:
            google_coursework_id = item["id"]

            # Verificar se existe
            existing = await coursework_repo.get_by_google_coursework_id(
                google_coursework_id
            )

            if not existing:
                # Criar coursework
                existing = await coursework_repo.create(
                    google_coursework_id=google_coursework_id,
                    course_id=course.id,
                    title=item.get("title", "Sem título"),
                    description=item.get("description"),
                    work_type=item.get("workType", "MATERIAL"),
                    state=item.get("state", "PUBLISHED"),
                    alternate_link=item.get("alternateLink"),
                )

            synced_count += 1

            # Extrair vídeos
            video_links = classroom_service.extract_video_links(item)

            for video_data in video_links:
                # Verificar se já existe
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
        logger.error(f"Erro ao sincronizar coursework: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sincronizar coursework: {str(e)}",
        )


@router.get("/{course_id}/coursework", response_model=List[CourseworkWithVideos])
async def list_coursework(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Lista materiais com vídeos de um curso
    """
    try:
        coursework_repo = CourseworkRepository(db)
        coursework_list = await coursework_repo.get_all_with_videos_by_course(course_id)

        return coursework_list

    except Exception as e:
        logger.error(f"Erro ao listar coursework: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar coursework",
        )
