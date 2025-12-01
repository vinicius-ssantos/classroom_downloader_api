# 📋 Classroom Downloader API - Especificação Completa

## 1. CONTEXTO DO PROJETO

### 1.1 Visão Geral
Criar um microserviço em Python/FastAPI para integração com Google Classroom, focado em descoberta e download automatizado de vídeos e materiais de cursos. Este serviço fará parte de um ecossistema maior que já inclui uma API principal para MyEdools.

### 1.2 Arquitetura do Sistema
```
┌─────────────────────────────────────┐
│   Frontend (Next.js)                │
│   - Interface única para o usuário  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│   API Principal (FastAPI)           │
│   Port: 8000                        │
│   - Gateway natural                 │
│   - MyEdools (nativo)               │
│   - Proxy para Classroom            │
└────────────────┬────────────────────┘
                 │
                 │ HTTP (interno)
                 ▼
┌─────────────────────────────────────┐
│   Classroom Downloader API          │ ← CRIAR ESTA API
│   Port: 8001                        │
│   - Google Classroom integration    │
│   - Video downloads                 │
│   - OAuth2 authentication           │
└─────────────────────────────────────┘
```

### 1.3 API Principal de Referência
A API principal está localizada em:
- Path: `/mnt/d/Users/vinic/PycharmProjects/MyEdools_Impacta/FastAPI_HeroSpark_MyEdools_Impacta`
- Arquitetura: Segue SOLID principles, Repository Pattern, Domain-Driven Design
- Stack: Python 3.11+, FastAPI 0.121+, SQLAlchemy 2.0 (async), PostgreSQL 16

**IMPORTANTE**: A nova API deve seguir os mesmos padrões arquiteturais da API principal para consistência.

---

## 2. REQUISITOS FUNCIONAIS

### 2.1 Autenticação Google OAuth2
**RF-001**: Implementar fluxo OAuth2 para autenticação com Google
- Suportar Authorization Code Flow
- Scopes necessários:
  - `https://www.googleapis.com/auth/classroom.courses.readonly`
  - `https://www.googleapis.com/auth/classroom.coursework.students.readonly`
  - `https://www.googleapis.com/auth/drive.readonly`
- Armazenar tokens de forma segura e criptografada
- Implementar refresh automático de tokens expirados

**RF-002**: Gerenciar múltiplas credenciais
- Suportar múltiplas contas Google simultaneamente
- Identificar credenciais por tenant_id
- Permitir revogação de credenciais

### 2.2 Descoberta de Cursos
**RF-003**: Listar cursos do Google Classroom
- Endpoint: `GET /courses`
- Query params: `credential_id`, `page_size`, `page_token`
- Retornar: id, nome, descrição, estado (ativo/arquivado), sala, professores
- Suportar paginação da API do Google

**RF-004**: Obter detalhes de um curso específico
- Endpoint: `GET /courses/{course_id}`
- Retornar metadados completos do curso

**RF-005**: Listar materiais/trabalhos de um curso
- Endpoint: `GET /courses/{course_id}/coursework`
- Incluir: assignments, materials, announcements
- Identificar materiais que contêm vídeos (YouTube, Drive)

### 2.3 Download de Vídeos
**RF-006**: Enfileirar download de vídeo
- Endpoint: `POST /downloads`
- Body: `{"course_id": "str", "coursework_id": "str", "credential_id": int}`
- Validar se o vídeo existe e é acessível
- Criar job de download em estado QUEUED
- Retornar: download_id, status, estimated_size

**RF-007**: Executar downloads com workers assíncronos
- Workers devem processar fila de downloads
- Suportar downloads de:
  - YouTube (videos embedded)
  - Google Drive (videos uploaded)
  - Links diretos de vídeo
- Usar yt-dlp para download
- Salvar metadados do vídeo (título, descrição, duração)

**RF-008**: Tracking de progresso de download
- Endpoint: `GET /downloads/{download_id}`
- Retornar: status (queued, running, completed, failed), progress_percent, file_path, error_message
- Atualizar progresso em tempo real durante download

**RF-009**: Listar downloads
- Endpoint: `GET /downloads`
- Query params: `status`, `course_id`, `credential_id`, `limit`, `offset`
- Retornar lista paginada de downloads

**RF-010**: Cancelar download
- Endpoint: `DELETE /downloads/{download_id}`
- Interromper download em andamento
- Limpar arquivos parciais

### 2.4 Batch Operations
**RF-011**: Download em lote de curso completo
- Endpoint: `POST /courses/{course_id}/download-all`
- Criar jobs para todos os vídeos do curso
- Retornar job_id do lote

**RF-012**: Status de batch download
- Endpoint: `GET /batch-downloads/{job_id}`
- Retornar: total de vídeos, completados, em progresso, falhados

### 2.5 Health & Monitoring
**RF-013**: Health check
- Endpoint: `GET /health`
- Verificar: conexão com DB, conexão com Google APIs, workers ativos

**RF-014**: Métricas Prometheus
- Endpoint: `GET /metrics`
- Expor: total downloads, downloads por status, bytes baixados, duração média

---

## 3. REQUISITOS NÃO-FUNCIONAIS

### 3.1 Performance
- **RNF-001**: Suportar até 10 downloads simultâneos
- **RNF-002**: API deve responder em < 200ms (exceto downloads)
- **RNF-003**: Workers devem ser escaláveis horizontalmente

### 3.2 Segurança
- **RNF-004**: Tokens OAuth2 devem ser criptografados em repouso
- **RNF-005**: Logs não devem conter tokens ou dados sensíveis
- **RNF-006**: Validar todos os inputs com Pydantic
- **RNF-007**: Usar HTTPS em produção

### 3.3 Confiabilidade
- **RNF-008**: Downloads falhados devem permitir retry
- **RNF-009**: Sistema deve recuperar de falhas de rede gracefully
- **RNF-010**: Tokens expirados devem ser renovados automaticamente

### 3.4 Manutenibilidade
- **RNF-011**: Seguir mesmos padrões da API principal (SOLID, Repository Pattern)
- **RNF-012**: Cobertura de testes > 80%
- **RNF-013**: Documentação OpenAPI automática (FastAPI)

---

## 4. STACK TECNOLÓGICA

### 4.1 Core
```python
# requirements.txt
fastapi==0.121.2
uvicorn[standard]==0.38.0
pydantic==2.10.5
pydantic-settings==2.7.1
python-multipart==0.0.20
```

### 4.2 Google APIs
```python
google-auth==2.37.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
google-api-python-client==2.159.0
```

### 4.3 Video Download
```python
yt-dlp==2024.12.23  # Melhor downloader, suporta Drive e YouTube
httpx==0.28.1       # HTTP async client
aiofiles==24.1.0    # Async file I/O
```

### 4.4 Database
```python
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
```

### 4.5 Workers & Queue
```python
# Opção 1 (recomendado): PostgreSQL-based queue (igual API principal)
# Sem dependências extras

# Opção 2 (alternativa): Redis-based
arq==0.26.1
redis==5.2.1
```

### 4.6 Utils
```python
python-jose[cryptography]==3.3.0  # JWT
python-dotenv==1.0.1
structlog==24.4.0                  # Structured logging
tenacity==9.0.0                    # Retry logic
cryptography==44.0.0               # Encryption
```

### 4.7 Testing
```python
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.28.1  # Para testes de API
faker==33.1.0
```

---

## 5. ARQUITETURA E PADRÕES

### 5.1 Estrutura de Diretórios
```
classroom-downloader-api/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings (env vars)
│   │   ├── logging.py              # Structured logging setup
│   │   ├── security.py             # Encryption/decryption utils
│   │   └── initializer.py          # App initialization logic
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py             # OAuth2 flow endpoints
│   │       ├── courses.py          # Course discovery endpoints
│   │       ├── coursework.py       # Coursework/materials endpoints
│   │       ├── downloads.py        # Download management endpoints
│   │       ├── batch_downloads.py  # Batch operations
│   │       ├── health.py           # Health check
│   │       └── metrics.py          # Prometheus metrics
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy Base
│   │   ├── database.py             # Engine, session factory
│   │   ├── models.py               # ORM models
│   │   └── dependencies.py         # DB dependencies (get_session)
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseRepository[T]
│   │   ├── credential.py           # CredentialRepository
│   │   ├── download.py             # DownloadRepository
│   │   └── batch_download.py       # BatchDownloadRepository
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── google_classroom.py     # Google Classroom API wrapper
│   │   ├── google_auth.py          # OAuth2 flow management
│   │   ├── video_downloader.py     # yt-dlp wrapper
│   │   ├── credential_manager.py   # Credential encryption/storage
│   │   └── download_orchestrator.py # Download coordination
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   └── value_objects.py        # CourseIdentifier, VideoSource, etc.
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                 # OAuth2 request/response schemas
│   │   ├── course.py               # Course schemas
│   │   ├── coursework.py           # Coursework schemas
│   │   └── download.py             # Download schemas
│   │
│   └── workers/
│       ├── __init__.py
│       └── download_worker.py      # Background download worker
│
├── migrations/                      # Alembic migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── unit/
│   │   ├── test_repositories.py
│   │   ├── test_services.py
│   │   └── test_video_downloader.py
│   └── integration/
│       ├── test_api_courses.py
│       ├── test_api_downloads.py
│       └── test_google_classroom.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml                  # Ruff, Black, mypy config
├── alembic.ini
└── README.md
```

### 5.2 Padrões Arquiteturais (seguir API principal)

#### Repository Pattern
```python
# app/repositories/base.py
from typing import Generic, TypeVar, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Base repository with CRUD operations"""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get(self, id: int) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def commit(self) -> None:
        await self.session.commit()

    # ... outros métodos CRUD
```

#### Service Layer
```python
# app/services/google_classroom.py
from googleapiclient.discovery import build
from app.repositories.credential import CredentialRepository

class GoogleClassroomService:
    """Service for Google Classroom API operations"""

    def __init__(
        self,
        credential_repo: CredentialRepository,
        credential_id: int
    ):
        self.credential_repo = credential_repo
        self.credential_id = credential_id

    async def list_courses(self) -> list[dict]:
        # Get credential
        credential = await self.credential_repo.get(self.credential_id)

        # Build Google API client
        service = build('classroom', 'v1', credentials=credential.to_google_creds())

        # Fetch courses
        results = service.courses().list(pageSize=100).execute()
        return results.get('courses', [])
```

#### Domain Objects
```python
# app/domain/value_objects.py
from dataclasses import dataclass
from enum import StrEnum

class VideoSource(StrEnum):
    YOUTUBE = "youtube"
    GOOGLE_DRIVE = "google_drive"
    DIRECT_LINK = "direct_link"

@dataclass(frozen=True)
class CourseIdentifier:
    """Value object for course identification"""
    course_id: str
    provider: str = "google_classroom"

    def __str__(self) -> str:
        return f"{self.provider}:{self.course_id}"

@dataclass(frozen=True)
class VideoMetadata:
    """Video metadata extracted from source"""
    title: str
    duration_seconds: int | None
    file_size_bytes: int | None
    format: str
    source: VideoSource
    source_url: str
```

---

## 6. MODELOS DE DADOS

### 6.1 Database Schema

```python
# app/db/models.py
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, Enum, Boolean, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum

class DownloadStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchDownloadStatus(enum.StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

class Credential(Base):
    """Google OAuth2 credentials storage"""
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # OAuth2 tokens (encrypted)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    client_id: Mapped[str] = mapped_column(String(512), nullable=False)
    client_secret: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, nullable=False)  # List of scopes

    # Metadata
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    downloads: Mapped[list["Download"]] = relationship(back_populates="credential")

class Course(Base):
    """Google Classroom course metadata"""
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  # Google's ID

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    room: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    state: Mapped[str] = mapped_column(String(50), nullable=False)  # ACTIVE, ARCHIVED, etc

    # Raw payload from Google API
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    coursework_items: Mapped[list["Coursework"]] = relationship(back_populates="course")

class Coursework(Base):
    """Course materials/assignments with videos"""
    __tablename__ = "coursework"

    id: Mapped[int] = mapped_column(primary_key=True)
    coursework_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Video info
    has_video: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # youtube, drive, etc

    # Metadata
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="coursework_items")
    downloads: Mapped[list["Download"]] = relationship(back_populates="coursework")

class Download(Base):
    """Individual video download tracking"""
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Relations
    credential_id: Mapped[int] = mapped_column(ForeignKey("credentials.id"), nullable=False)
    coursework_id: Mapped[int] = mapped_column(ForeignKey("coursework.id"), nullable=False)
    batch_download_id: Mapped[int | None] = mapped_column(ForeignKey("batch_downloads.id"), nullable=True)

    # Download info
    status: Mapped[DownloadStatus] = mapped_column(Enum(DownloadStatus), default=DownloadStatus.QUEUED, nullable=False, index=True)
    video_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Progress
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downloaded_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Output
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata
    video_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    credential: Mapped["Credential"] = relationship(back_populates="downloads")
    coursework: Mapped["Coursework"] = relationship(back_populates="downloads")
    batch_download: Mapped["BatchDownload | None"] = relationship(back_populates="downloads")

class BatchDownload(Base):
    """Batch download of entire course"""
    __tablename__ = "batch_downloads"

    id: Mapped[int] = mapped_column(primary_key=True)

    course_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    credential_id: Mapped[int] = mapped_column(ForeignKey("credentials.id"), nullable=False)

    status: Mapped[BatchDownloadStatus] = mapped_column(Enum(BatchDownloadStatus), default=BatchDownloadStatus.PENDING, nullable=False)

    # Stats
    total_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    downloads: Mapped[list["Download"]] = relationship(back_populates="batch_download")
```

---

## 7. IMPLEMENTAÇÃO DETALHADA

### 7.1 Configuração (app/core/config.py)

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Classroom Downloader API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/classroom",
        description="PostgreSQL connection string"
    )

    # Google OAuth2
    google_client_id: str = Field(..., description="Google OAuth2 client ID")
    google_client_secret: str = Field(..., description="Google OAuth2 client secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8001/auth/callback",
        description="OAuth2 redirect URI"
    )
    google_scopes: list[str] = Field(
        default=[
            "https://www.googleapis.com/auth/classroom.courses.readonly",
            "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )

    # Security
    encryption_key: str = Field(..., description="Fernet encryption key for credentials")

    # Downloads
    download_dir: str = Field(default="/app/downloads", description="Directory for downloaded videos")
    max_concurrent_downloads: int = Field(default=5, description="Max simultaneous downloads")
    download_timeout_seconds: int = Field(default=3600, description="Download timeout (1 hour)")

    # Workers
    worker_poll_interval_seconds: int = Field(default=5, description="Worker queue polling interval")
    worker_max_retries: int = Field(default=3, description="Max download retries")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # yt-dlp
    ytdlp_format: str = Field(
        default="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        description="yt-dlp format selector"
    )
    ytdlp_output_template: str = Field(
        default="%(id)s.%(ext)s",
        description="yt-dlp output filename template"
    )
```

### 7.2 Serviço Google Classroom (app/services/google_classroom.py)

```python
import logging
from typing import Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from app.repositories.credential import CredentialRepository
from app.core.security import decrypt_token

logger = logging.getLogger(__name__)

class GoogleClassroomService:
    """Service for interacting with Google Classroom API"""

    def __init__(
        self,
        credential_repo: CredentialRepository,
        credential_id: int,
        encryption_key: str,
    ):
        self.credential_repo = credential_repo
        self.credential_id = credential_id
        self.encryption_key = encryption_key
        self._service = None

    async def _get_service(self):
        """Get or create Google Classroom API service"""
        if self._service is not None:
            return self._service

        # Get credential from DB
        credential = await self.credential_repo.get(self.credential_id)
        if not credential:
            raise ValueError(f"Credential {self.credential_id} not found")

        # Decrypt tokens
        access_token = decrypt_token(credential.access_token, self.encryption_key)
        refresh_token = decrypt_token(credential.refresh_token, self.encryption_key) if credential.refresh_token else None

        # Create Google credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=credential.token_uri,
            client_id=credential.client_id,
            client_secret=credential.client_secret,
            scopes=credential.scopes,
        )

        # Build service
        self._service = build('classroom', 'v1', credentials=creds)
        return self._service

    async def list_courses(
        self,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """
        List courses from Google Classroom

        Returns:
            {
                "courses": [...],
                "nextPageToken": "..."
            }
        """
        try:
            service = await self._get_service()

            results = service.courses().list(
                pageSize=page_size,
                pageToken=page_token,
            ).execute()

            return {
                "courses": results.get('courses', []),
                "nextPageToken": results.get('nextPageToken'),
            }

        except HttpError as e:
            logger.error(f"Google Classroom API error: {e}", exc_info=True)
            raise

    async def get_course(self, course_id: str) -> dict[str, Any]:
        """Get course details"""
        try:
            service = await self._get_service()
            course = service.courses().get(id=course_id).execute()
            return course
        except HttpError as e:
            logger.error(f"Failed to get course {course_id}: {e}", exc_info=True)
            raise

    async def list_coursework(
        self,
        course_id: str,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """
        List coursework (assignments, materials) for a course

        Returns:
            {
                "courseWork": [...],
                "nextPageToken": "..."
            }
        """
        try:
            service = await self._get_service()

            results = service.courses().courseWork().list(
                courseId=course_id,
                pageSize=page_size,
                pageToken=page_token,
            ).execute()

            return {
                "courseWork": results.get('courseWork', []),
                "nextPageToken": results.get('nextPageToken'),
            }

        except HttpError as e:
            logger.error(f"Failed to list coursework for {course_id}: {e}", exc_info=True)
            raise

    async def extract_video_urls(self, coursework_item: dict) -> list[str]:
        """
        Extract video URLs from coursework materials

        Args:
            coursework_item: Raw coursework dict from Google API

        Returns:
            List of video URLs (YouTube, Drive, etc)
        """
        video_urls = []

        # Check materials
        materials = coursework_item.get('materials', [])
        for material in materials:
            # YouTube video
            if 'youtubeVideo' in material:
                video_id = material['youtubeVideo'].get('id')
                if video_id:
                    video_urls.append(f"https://www.youtube.com/watch?v={video_id}")

            # Google Drive file
            elif 'driveFile' in material:
                drive_file = material['driveFile'].get('driveFile', {})
                # Check if it's a video mimetype
                mime_type = drive_file.get('mimeType', '')
                if mime_type.startswith('video/'):
                    file_id = drive_file.get('id')
                    if file_id:
                        video_urls.append(f"https://drive.google.com/file/d/{file_id}/view")

            # Link (might be video)
            elif 'link' in material:
                url = material['link'].get('url')
                if url and ('youtube.com' in url or 'youtu.be' in url or 'drive.google.com' in url):
                    video_urls.append(url)

        return video_urls
```

### 7.3 Serviço de Download (app/services/video_downloader.py)

```python
import logging
import asyncio
from pathlib import Path
from typing import Callable

import yt_dlp
from yt_dlp.utils import DownloadError

from app.domain.value_objects import VideoMetadata, VideoSource

logger = logging.getLogger(__name__)

class VideoDownloadError(Exception):
    """Custom exception for video download failures"""
    pass

class VideoDownloader:
    """Service for downloading videos using yt-dlp"""

    def __init__(
        self,
        download_dir: str,
        format_selector: str,
        output_template: str,
    ):
        self.download_dir = Path(download_dir)
        self.format_selector = format_selector
        self.output_template = output_template

        # Ensure download dir exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_video(
        self,
        url: str,
        progress_callback: Callable[[dict], None] | None = None,
    ) -> tuple[str, VideoMetadata]:
        """
        Download video from URL

        Args:
            url: Video URL (YouTube, Drive, etc)
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (file_path, metadata)

        Raises:
            VideoDownloadError: If download fails
        """

        def progress_hook(d: dict):
            """Called by yt-dlp during download"""
            if d['status'] == 'downloading':
                if progress_callback:
                    progress_data = {
                        'status': 'downloading',
                        'downloaded_bytes': d.get('downloaded_bytes', 0),
                        'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate', 0),
                        'speed': d.get('speed', 0),
                        'eta': d.get('eta', 0),
                    }
                    progress_callback(progress_data)

            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback({'status': 'finished', 'filename': d['filename']})

        ydl_opts = {
            'format': self.format_selector,
            'outtmpl': str(self.download_dir / self.output_template),
            'progress_hooks': [progress_hook],
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            # Quality settings
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Thumbnail
            'writethumbnail': True,
            'embedthumbnail': True,
            # Subtitles
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['pt', 'en'],
        }

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._download_sync,
                url,
                ydl_opts,
            )

            file_path = result['file_path']
            metadata = VideoMetadata(
                title=result['title'],
                duration_seconds=result.get('duration'),
                file_size_bytes=result.get('filesize') or result.get('filesize_approx'),
                format=result.get('ext', 'mp4'),
                source=self._detect_source(url),
                source_url=url,
            )

            return file_path, metadata

        except DownloadError as e:
            logger.error(f"yt-dlp download failed for {url}: {e}", exc_info=True)
            raise VideoDownloadError(f"Download failed: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}", exc_info=True)
            raise VideoDownloadError(f"Unexpected error: {e}") from e

    def _download_sync(self, url: str, ydl_opts: dict) -> dict:
        """Synchronous download (runs in executor)"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading first
            info = ydl.extract_info(url, download=False)

            # Now download
            ydl.download([url])

            # Get output filename
            filename = ydl.prepare_filename(info)

            return {
                'file_path': filename,
                'title': info.get('title'),
                'duration': info.get('duration'),
                'filesize': info.get('filesize'),
                'filesize_approx': info.get('filesize_approx'),
                'ext': info.get('ext'),
            }

    @staticmethod
    def _detect_source(url: str) -> VideoSource:
        """Detect video source from URL"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return VideoSource.YOUTUBE
        elif 'drive.google.com' in url:
            return VideoSource.GOOGLE_DRIVE
        else:
            return VideoSource.DIRECT_LINK

    async def get_video_info(self, url: str) -> dict:
        """
        Extract video info without downloading

        Returns:
            Video metadata dict
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_info_sync,
                url,
                ydl_opts,
            )
            return info

        except Exception as e:
            logger.error(f"Failed to extract info from {url}: {e}", exc_info=True)
            raise

    def _extract_info_sync(self, url: str, ydl_opts: dict) -> dict:
        """Synchronous info extraction"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
```

### 7.4 Router de Downloads (app/api/routers/downloads.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_session
from app.schemas.download import (
    DownloadCreateRequest,
    DownloadResponse,
    DownloadListResponse,
)
from app.services.download_orchestrator import DownloadOrchestrator
from app.repositories.download import DownloadRepository
from app.db.models import DownloadStatus

router = APIRouter(prefix="/downloads", tags=["downloads"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=DownloadResponse)
async def create_download(
    request: DownloadCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> DownloadResponse:
    """
    Enqueue a video download

    Creates a download job and adds it to the queue.
    Workers will process it asynchronously.
    """
    orchestrator = DownloadOrchestrator(session)
    download = await orchestrator.enqueue_download(
        credential_id=request.credential_id,
        coursework_id=request.coursework_id,
    )

    return DownloadResponse.from_orm(download)

@router.get("/{download_id}", response_model=DownloadResponse)
async def get_download_status(
    download_id: int,
    session: AsyncSession = Depends(get_session),
) -> DownloadResponse:
    """Get download status and progress"""
    repo = DownloadRepository(session)
    download = await repo.get(download_id)

    if not download:
        raise HTTPException(status_code=404, detail="Download not found")

    return DownloadResponse.from_orm(download)

@router.get("", response_model=DownloadListResponse)
async def list_downloads(
    status: DownloadStatus | None = None,
    credential_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> DownloadListResponse:
    """List downloads with optional filters"""
    repo = DownloadRepository(session)

    downloads = await repo.list_with_filters(
        status=status,
        credential_id=credential_id,
        limit=limit,
        offset=offset,
    )

    total = await repo.count_with_filters(
        status=status,
        credential_id=credential_id,
    )

    return DownloadListResponse(
        downloads=[DownloadResponse.from_orm(d) for d in downloads],
        total=total,
        limit=limit,
        offset=offset,
    )

@router.delete("/{download_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_download(
    download_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Cancel a download (if running) or remove from queue"""
    orchestrator = DownloadOrchestrator(session)
    await orchestrator.cancel_download(download_id)
```

### 7.5 Worker de Download (app/workers/download_worker.py)

```python
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.models import Download, DownloadStatus
from app.repositories.download import DownloadRepository
from app.services.video_downloader import VideoDownloader, VideoDownloadError

logger = logging.getLogger(__name__)

class DownloadWorker:
    """Background worker for processing download queue"""

    def __init__(
        self,
        settings: Settings,
        max_concurrent: int = 5,
    ):
        self.settings = settings
        self.max_concurrent = max_concurrent
        self.running = False

        # Database setup
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Video downloader
        self.downloader = VideoDownloader(
            download_dir=settings.download_dir,
            format_selector=settings.ytdlp_format,
            output_template=settings.ytdlp_output_template,
        )

    async def start(self):
        """Start the worker loop"""
        self.running = True
        logger.info(f"Starting download worker (max_concurrent={self.max_concurrent})")

        while self.running:
            try:
                await self._process_queue()
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)

            # Poll interval
            await asyncio.sleep(self.settings.worker_poll_interval_seconds)

    async def stop(self):
        """Stop the worker gracefully"""
        logger.info("Stopping download worker...")
        self.running = False

    async def _process_queue(self):
        """Process queued downloads"""
        async with self.async_session() as session:
            repo = DownloadRepository(session)

            # Get queued downloads
            queued = await repo.get_queued_downloads(limit=self.max_concurrent)

            if not queued:
                return

            logger.info(f"Processing {len(queued)} downloads")

            # Process concurrently
            tasks = [self._process_download(download.id) for download in queued]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_download(self, download_id: int):
        """Process a single download"""
        async with self.async_session() as session:
            repo = DownloadRepository(session)
            download = await repo.get(download_id)

            if not download or download.status != DownloadStatus.QUEUED:
                return

            # Mark as running
            download.status = DownloadStatus.RUNNING
            download.started_at = datetime.now(timezone.utc)
            await repo.commit()

            logger.info(f"Starting download {download_id}: {download.video_url}")

            try:
                # Progress callback
                def on_progress(progress_data: dict):
                    asyncio.create_task(self._update_progress(download_id, progress_data))

                # Download video
                file_path, metadata = await self.downloader.download_video(
                    url=download.video_url,
                    progress_callback=on_progress,
                )

                # Update success
                download.status = DownloadStatus.COMPLETED
                download.file_path = file_path
                download.file_size_bytes = metadata.file_size_bytes
                download.video_metadata = {
                    'title': metadata.title,
                    'duration_seconds': metadata.duration_seconds,
                    'format': metadata.format,
                    'source': metadata.source,
                }
                download.progress_percent = 100
                download.completed_at = datetime.now(timezone.utc)
                await repo.commit()

                logger.info(f"Download {download_id} completed: {file_path}")

            except VideoDownloadError as e:
                # Download failed
                logger.error(f"Download {download_id} failed: {e}")

                download.status = DownloadStatus.FAILED
                download.error_message = str(e)
                download.retry_count += 1

                # Requeue if under retry limit
                if download.retry_count < self.settings.worker_max_retries:
                    download.status = DownloadStatus.QUEUED
                    logger.info(f"Requeuing download {download_id} (retry {download.retry_count})")

                await repo.commit()

            except Exception as e:
                logger.error(f"Unexpected error in download {download_id}: {e}", exc_info=True)

                download.status = DownloadStatus.FAILED
                download.error_message = f"Unexpected error: {e}"
                await repo.commit()

    async def _update_progress(self, download_id: int, progress_data: dict):
        """Update download progress in database"""
        async with self.async_session() as session:
            repo = DownloadRepository(session)
            download = await repo.get(download_id)

            if not download:
                return

            downloaded = progress_data.get('downloaded_bytes', 0)
            total = progress_data.get('total_bytes', 0)

            download.downloaded_bytes = downloaded
            download.total_bytes = total if total > 0 else None

            if total > 0:
                download.progress_percent = int((downloaded / total) * 100)

            await repo.commit()

# Entry point for running worker
async def run_worker():
    """Run the download worker"""
    from app.core.config import Settings

    settings = Settings()
    worker = DownloadWorker(
        settings=settings,
        max_concurrent=settings.max_concurrent_downloads,
    )

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()

if __name__ == "__main__":
    asyncio.run(run_worker())
```

---

## 8. DOCKER & DEPLOYMENT

### 8.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create downloads directory
RUN mkdir -p /app/downloads

# Expose port
EXPOSE 8001

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 8.2 docker-compose.yml

```yaml
version: '3.8'

services:
  classroom-api:
    build: .
    container_name: classroom-downloader-api
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/classroom
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - GOOGLE_REDIRECT_URI=http://localhost:8001/auth/callback
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DOWNLOAD_DIR=/app/downloads
      - LOG_LEVEL=INFO
    volumes:
      - ./downloads:/app/downloads
    depends_on:
      - postgres
    networks:
      - backend

  classroom-worker:
    build: .
    container_name: classroom-download-worker
    command: python -m app.workers.download_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/classroom
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DOWNLOAD_DIR=/app/downloads
      - MAX_CONCURRENT_DOWNLOADS=5
      - LOG_LEVEL=INFO
    volumes:
      - ./downloads:/app/downloads
    depends_on:
      - postgres
      - classroom-api
    networks:
      - backend

  postgres:
    image: postgres:16
    container_name: postgres-classroom
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=classroom
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend

volumes:
  postgres_data:

networks:
  backend:
    driver: bridge
```

---

## 9. TESTES

### 9.1 Estrutura de Testes

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.core.config import Settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    settings = Settings()
    engine = create_async_engine(
        settings.database_url.replace("/classroom", "/classroom_test"),
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def session(engine):
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()

# tests/unit/test_video_downloader.py
import pytest
from app.services.video_downloader import VideoDownloader, VideoDownloadError

@pytest.mark.asyncio
async def test_extract_video_info():
    downloader = VideoDownloader(
        download_dir="/tmp/downloads",
        format_selector="best",
        output_template="%(id)s.%(ext)s",
    )

    # Test with a known video
    info = await downloader.get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert 'title' in info
    assert 'duration' in info
    assert info['duration'] > 0

# tests/integration/test_api_downloads.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_download(session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/downloads",
            json={
                "credential_id": 1,
                "coursework_id": 1,
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['status'] == 'queued'
        assert 'id' in data
```

---

## 10. DOCUMENTAÇÃO

### 10.1 README.md

```markdown
# Classroom Downloader API

Microserviço para download automatizado de vídeos do Google Classroom.

## Funcionalidades

- 🔐 Autenticação OAuth2 com Google
- 📚 Descoberta de cursos e materiais
- 📥 Download de vídeos (YouTube, Google Drive)
- ⚡ Workers assíncronos para downloads paralelos
- 📊 Tracking de progresso em tempo real
- 🔄 Retry automático em caso de falha

## Stack

- Python 3.11+
- FastAPI 0.121+
- SQLAlchemy 2.0 (async)
- PostgreSQL 16
- yt-dlp
- Google APIs

## Quickstart

### 1. Setup

```bash
# Clone
git clone <repo>
cd classroom-downloader-api

# Environment
cp .env.example .env
# Edite .env com suas credenciais

# Docker
docker-compose up --build
```

### 2. OAuth2 Setup

1. Crie projeto no Google Cloud Console
2. Habilite Classroom API e Drive API
3. Crie credenciais OAuth2
4. Configure redirect URI: `http://localhost:8001/auth/callback`
5. Adicione client ID e secret no `.env`

### 3. API Docs

- OpenAPI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Desenvolvimento

```bash
# Install deps
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run API
uvicorn app.main:app --reload

# Run worker
python -m app.workers.download_worker

# Run tests
pytest
pytest --cov=app tests/
```

## Arquitetura

```
API (8001) ← HTTP ← API Principal (8000) ← HTTP ← Frontend
    ↓
PostgreSQL
    ↑
Worker (background)
```

## License

MIT
```

---

## 11. CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Setup Inicial (1-2 dias)
- [ ] Criar estrutura de diretórios
- [ ] Configurar `requirements.txt`
- [ ] Criar `Dockerfile` e `docker-compose.yml`
- [ ] Setup de configuração (`core/config.py`)
- [ ] Setup de logging
- [ ] Criar modelos do banco (`db/models.py`)
- [ ] Configurar Alembic (migrations)

### Fase 2: Autenticação Google (2-3 dias)
- [ ] Implementar `GoogleAuthService` (OAuth2 flow)
- [ ] Criar `CredentialRepository`
- [ ] Implementar encryption/decryption de tokens
- [ ] Criar rotas de auth (`/auth/login`, `/auth/callback`)
- [ ] Testar fluxo OAuth2

### Fase 3: Google Classroom Integration (2-3 dias)
- [ ] Implementar `GoogleClassroomService`
- [ ] Criar rotas de cursos (`/courses`)
- [ ] Criar rotas de coursework (`/courses/{id}/coursework`)
- [ ] Implementar extração de URLs de vídeos
- [ ] Criar repositories e schemas necessários

### Fase 4: Download de Vídeos (3-4 dias)
- [ ] Implementar `VideoDownloader` (yt-dlp wrapper)
- [ ] Criar `DownloadOrchestrator`
- [ ] Implementar rotas de download (`/downloads`)
- [ ] Criar `DownloadWorker`
- [ ] Implementar tracking de progresso
- [ ] Testar downloads (YouTube e Drive)

### Fase 5: Batch Downloads (1-2 dias)
- [ ] Implementar batch download logic
- [ ] Criar rotas de batch (`/courses/{id}/download-all`)
- [ ] Testar com curso completo

### Fase 6: Testes (2-3 dias)
- [ ] Escrever testes unitários (repositories, services)
- [ ] Escrever testes de integração (API endpoints)
- [ ] Alcançar > 80% coverage

### Fase 7: Documentação e Deploy (1-2 dias)
- [ ] Escrever README completo
- [ ] Documentar APIs no código
- [ ] Configurar CI/CD (opcional)
- [ ] Deploy em ambiente de teste

### Fase 8: Integração com API Principal (1-2 dias)
- [ ] Criar `ClassroomServiceClient` na API principal
- [ ] Criar rotas de proxy na API principal
- [ ] Criar rota agregada de cursos
- [ ] Testar integração end-to-end

**Total estimado: 15-22 dias de desenvolvimento**

---

## 12. CONSIDERAÇÕES FINAIS

### Pontos de Atenção
1. **Quotas do Google**: A Google Classroom API tem limites de requisições. Implementar caching se necessário.
2. **Tamanho de vídeos**: Vídeos grandes podem demorar. Implementar timeouts apropriados.
3. **Credenciais expiradas**: Implementar renovação automática de tokens OAuth2.
4. **Cleanup**: Implementar job para limpar vídeos antigos se necessário.

### Melhorias Futuras
- [ ] Suporte a outras fontes (Vimeo, etc)
- [ ] Compressão de vídeos
- [ ] Thumbnails e metadados
- [ ] Notificações quando download completar
- [ ] API de webhooks para notificar API principal
- [ ] Dashboard admin

---

**FIM DA ESPECIFICAÇÃO**
