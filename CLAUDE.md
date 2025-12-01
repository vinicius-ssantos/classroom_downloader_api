# CLAUDE.md - AI Assistant Guide

> Comprehensive guide for AI assistants working with the Classroom Downloader API codebase

**Last Updated:** 2025-12-01
**Project Version:** 1.0.0
**Python Version:** 3.11+

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Directory Structure](#architecture--directory-structure)
3. [Technology Stack](#technology-stack)
4. [Database Models & Relationships](#database-models--relationships)
5. [Service Layer Patterns](#service-layer-patterns)
6. [API Endpoints](#api-endpoints)
7. [Background Worker System](#background-worker-system)
8. [Development Workflows](#development-workflows)
9. [Code Conventions](#code-conventions)
10. [Common Tasks](#common-tasks)
11. [Important Context & Gotchas](#important-context--gotchas)
12. [Future Improvements](#future-improvements)

---

## Project Overview

### Purpose
A FastAPI microservice for automated downloading of videos from Google Classroom courses. The system:
- Authenticates with Google using cookies (OAuth2 support exists but is disabled)
- Discovers courses and coursework via Google Classroom API
- Extracts video links from course materials
- Downloads videos asynchronously using yt-dlp
- Tracks download progress in PostgreSQL

### Current State
- **Status:** MVP / Development
- **Primary Use:** Personal/single-user deployment
- **Authentication:** Cookie-based (manual import)
- **Deployment:** Docker-ready, not production-hardened

### Key Features
✅ Google Classroom API integration
✅ Async video downloads with yt-dlp
✅ Background worker for job processing
✅ Progress tracking & retry logic
✅ PostgreSQL with SQLAlchemy 2.0 (async)
✅ Containerized with Docker
⚠️ Cookie-based auth (OAuth2 commented out)
⚠️ Single worker instance
⚠️ No tests implemented yet

---

## Architecture & Directory Structure

### High-Level Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   FastAPI   │────────>│  PostgreSQL  │<────────│   Worker    │
│   Routers   │         │   Database   │         │  Background │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │                        │                        │
      v                        v                        v
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Services   │────────>│ Repositories │         │   yt-dlp    │
│  (Business  │         │   (Data      │         │  (Download) │
│   Logic)    │         │   Access)    │         └─────────────┘
└─────────────┘         └──────────────┘
      │
      v
┌─────────────┐
│ Google APIs │
│ (Classroom, │
│   Drive)    │
└─────────────┘
```

### Directory Structure

```
classroom-downloader-api/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app factory & lifespan
│   │
│   ├── api/
│   │   ├── routers/
│   │   │   ├── auth.py             # OAuth2 endpoints (DISABLED)
│   │   │   ├── courses.py          # Course endpoints (OAuth2 version)
│   │   │   ├── courses_simple.py   # Course endpoints (cookies) ✅ ACTIVE
│   │   │   ├── downloads.py        # Download job endpoints
│   │   │   └── health.py           # Health check endpoints
│   │   └── __init__.py
│   │
│   ├── core/
│   │   ├── config.py               # Pydantic Settings configuration
│   │   └── __init__.py
│   │
│   ├── db/
│   │   ├── database.py             # Async SQLAlchemy setup
│   │   └── __init__.py
│   │
│   ├── domain/
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── __init__.py
│   │
│   ├── repositories/               # Data Access Layer
│   │   ├── base.py                 # Generic CRUD operations
│   │   ├── course_repository.py
│   │   ├── coursework_repository.py
│   │   ├── download_job_repository.py
│   │   ├── user_repository.py
│   │   ├── video_link_repository.py
│   │   └── __init__.py
│   │
│   ├── schemas/                    # Pydantic schemas (DTOs)
│   │   ├── auth.py
│   │   ├── course.py
│   │   ├── coursework.py
│   │   ├── download.py
│   │   ├── user.py
│   │   ├── video_link.py
│   │   └── __init__.py
│   │
│   ├── services/                   # Business Logic Layer
│   │   ├── cookie_manager.py      # Cookie storage (NOT encrypted yet)
│   │   ├── credentials_manager.py # OAuth2 credential encryption
│   │   ├── google_classroom.py    # OAuth2 version (DISABLED)
│   │   ├── google_classroom_simple.py  # Cookie-based ✅ ACTIVE
│   │   ├── http_client.py         # Shared HTTP client
│   │   ├── video_downloader.py    # yt-dlp wrapper
│   │   └── __init__.py
│   │
│   └── workers/
│       ├── download_worker.py      # Background job processor
│       └── __init__.py
│
├── migrations/                      # Alembic database migrations
│   ├── env.py
│   └── versions/
│
├── tests/                          # Test suite (EMPTY - needs implementation)
│   ├── integration/
│   ├── unit/
│   └── __init__.py
│
├── .env.example                    # Environment variables template
├── alembic.ini                     # Alembic configuration
├── Dockerfile                      # Container definition
├── requirements.txt                # Python dependencies
├── README.md                       # User-facing documentation
├── PLANO_MELHORIAS.md             # Improvement roadmap (Portuguese)
└── CLAUDE.md                       # This file
```

---

## Technology Stack

### Core Framework
- **FastAPI 0.121.2** - Async web framework
- **Uvicorn 0.38.0** - ASGI server
- **Pydantic 2.10.5** - Data validation & settings
- **Python 3.11+** - Runtime

### Database
- **PostgreSQL 16** - Primary database
- **SQLAlchemy 2.0.36** (async) - ORM
- **asyncpg 0.30.0** - Async PostgreSQL driver
- **Alembic 1.14.0** - Database migrations

### Google APIs
- **google-api-python-client 2.159.0** - Google API client
- **google-auth 2.37.0** - Authentication
- **google-auth-oauthlib 1.2.1** - OAuth2 flow

### Video Download
- **yt-dlp 2024.12.23** - Video downloader (supports Google Drive)
- **FFmpeg** - Video processing (system dependency)

### Utilities
- **httpx 0.28.1** - Async HTTP client
- **aiofiles 24.1.0** - Async file I/O
- **cryptography 44.0.0** - Encryption (for credentials)
- **tenacity 9.0.0** - Retry logic
- **structlog 24.4.0** - Structured logging

### Development
- **pytest 8.3.4** - Testing framework (not yet implemented)
- **pytest-asyncio 0.24.0** - Async test support
- **faker 33.1.0** - Test data generation

---

## Database Models & Relationships

### Entity Relationship Diagram

```
User (1) ──────< (N) Course (1) ──────< (N) Coursework (1) ──────< (N) VideoLink
  │                      │                                                    │
  │                      │                                                    │
  └──────< (N) DownloadJob (N) >──────┘                                      │
                  │                                                           │
                  └───────────────────────────────────────────────────────────┘
```

### Models Overview

#### **User** (`app/domain/models.py:35-81`)
Stores Google account information and encrypted OAuth2 credentials.

**Key Fields:**
- `email` - Google account email (unique)
- `google_id` - Google user ID (unique)
- `encrypted_credentials` - Fernet-encrypted OAuth2 tokens (Text, nullable)
- `last_login` - Last authentication timestamp

**Relationships:**
- `courses` (1:N) - User's Google Classroom courses
- `download_jobs` (1:N) - User's download jobs

**Important:** Currently NOT used for authentication. Cookie-based auth bypasses user creation.

---

#### **Course** (`app/domain/models.py:83-137`)
Represents a Google Classroom course.

**Key Fields:**
- `google_course_id` - Google's course identifier (unique)
- `name` - Course name
- `state` - Course state (ACTIVE, ARCHIVED, etc.)
- `last_synced_at` - Last synchronization timestamp
- `owner_id` - Foreign key to User

**Relationships:**
- `user` (N:1) - Course owner
- `coursework` (1:N) - Course materials/assignments
- `download_jobs` (1:N) - Download jobs for this course

**Router:** `courses_simple.router`

---

#### **Coursework** (`app/domain/models.py:139-186`)
Represents course materials, assignments, or announcements.

**Key Fields:**
- `google_coursework_id` - Google's coursework identifier (unique)
- `title` - Coursework title
- `work_type` - Type (ASSIGNMENT, MATERIAL, etc.)
- `state` - State (PUBLISHED, DRAFT, DELETED)
- `due_date` - Due date for assignments (nullable)
- `course_id` - Foreign key to Course

**Relationships:**
- `course` (N:1) - Parent course
- `video_links` (1:N) - Video URLs extracted from description/materials

**Note:** Video extraction happens during coursework sync.

---

#### **VideoLink** (`app/domain/models.py:188-233`)
Stores video URLs extracted from coursework materials.

**Key Fields:**
- `url` - Video URL (max 1024 chars)
- `source_type` - Source type (youtube, drive, vimeo, etc.)
- `drive_file_id` - Google Drive file ID (for Drive videos)
- `is_downloaded` - Download completion flag
- `download_path` - Path to downloaded file
- `coursework_id` - Foreign key to Coursework

**Relationships:**
- `coursework` (N:1) - Parent coursework
- `download_jobs` (1:N) - Download attempts for this video

**Extraction Logic:** `app/services/google_classroom_simple.py:_extract_video_links_from_coursework()`

---

#### **DownloadJob** (`app/domain/models.py:235-295`)
Tracks individual video download tasks.

**Key Fields:**
- `status` - Enum: PENDING, DOWNLOADING, COMPLETED, FAILED, CANCELLED
- `progress_percent` - Download progress (0-100)
- `downloaded_bytes` / `total_bytes` - Download size tracking
- `retry_count` - Number of retry attempts
- `error_message` - Last error (if failed)
- `output_path` - Path to downloaded file
- `started_at` / `completed_at` - Timestamps

**Relationships:**
- `user` (N:1) - Job owner
- `course` (N:1) - Related course
- `video_link` (N:1) - Video being downloaded

**Worker:** Processed by `DownloadWorker` (`app/workers/download_worker.py`)

---

### Database Connection & Sessions

**Configuration:** `app/db/database.py`

```python
# Async engine with connection pooling
engine = create_async_engine(
    settings.database_url,  # postgresql+asyncpg://...
    echo=settings.debug,
    pool_pre_ping=True,
)

# Session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Context manager for scoped sessions
@asynccontextmanager
async def get_db_context() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Usage in Routers:**
```python
# Dependency injection
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_db_context() as session:
        yield session

# In endpoint
@router.get("/courses")
async def list_courses(db: AsyncSession = Depends(get_db_session)):
    repo = CourseRepository(Course, db)
    return await repo.get_all()
```

---

## Service Layer Patterns

### Repository Pattern

**Base Repository:** `app/repositories/base.py`

Generic CRUD operations for all entities:
- `get(id)` - Fetch by ID
- `get_all(skip, limit)` - Paginated list
- `create(**kwargs)` - Create new record
- `update(id, **kwargs)` - Update existing
- `delete(id)` - Delete record
- `count()` - Total count

**Example:**
```python
class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: AsyncSession):
        super().__init__(Course, db)

    async def get_by_google_id(self, google_course_id: str) -> Optional[Course]:
        result = await self.db.execute(
            select(Course).where(Course.google_course_id == google_course_id)
        )
        return result.scalar_one_or_none()
```

**Pattern:** All repositories extend `BaseRepository` and add domain-specific queries.

---

### Service Layer

#### **VideoDownloaderService** (`app/services/video_downloader.py:35-291`)

Wraps yt-dlp for async video downloads.

**Key Methods:**
- `download_video(url, output_subdir, progress_callback)` - Download with progress tracking
- `get_video_info(url)` - Extract video metadata without downloading
- `is_supported_url(url)` - Check if yt-dlp supports URL

**Features:**
- Retry logic with exponential backoff (tenacity)
- Progress callbacks for real-time updates
- Runs yt-dlp in thread pool to avoid blocking event loop
- Automatic MP4 conversion with FFmpeg

**Important:** Singleton pattern - use `get_video_downloader()` to get instance.

---

#### **GoogleClassroomSimpleService** (`app/services/google_classroom_simple.py`)

**Active** cookie-based Google Classroom API client.

**Key Methods:**
- `list_courses()` - Fetch user's courses
- `list_coursework(course_id)` - Fetch course materials
- `_extract_video_links_from_coursework(coursework)` - Parse video URLs from materials

**Authentication:** Uses cookies loaded from `cookies.json` via `CookieManager`.

**Video Extraction Logic:**
- Parses `description`, `materials`, and `attachments` fields
- Supports: YouTube, Google Drive videos, Vimeo
- Regex patterns in `_extract_video_links_from_text()`

---

#### **CookieManager** (`app/services/cookie_manager.py`)

Manages Google authentication cookies.

**Storage:** `cookies.json` (plaintext - NOT encrypted yet!)

**Required Cookies:**
- `SID`, `HSID`, `SSID`, `APISID`, `SAPISID`

**Import Script:** `import_cookies.py` - Helper to import from browser export.

**⚠️ Security Issue:** Cookies stored unencrypted. See `PLANO_MELHORIAS.md` for encryption plan.

---

## API Endpoints

### Health Endpoints (`/health`)

**Router:** `app/api/routers/health.py`

```
GET /health        - Basic health check (always returns 200)
GET /health/db     - Database connection check
```

**Usage:** Kubernetes liveness/readiness probes.

---

### Courses Endpoints (`/courses`)

**Router:** `app/api/routers/courses_simple.py` (active)

```
GET  /courses?user_id={user_id}
     - List all courses with statistics (video count, download progress)

POST /courses/sync?user_id={user_id}
     - Sync courses from Google Classroom API
     - Creates/updates Course records in database

GET  /courses/{course_id}
     - Get course details with coursework

POST /courses/{course_id}/sync-coursework?user_id={user_id}
     - Sync coursework and extract video links
     - Creates Coursework and VideoLink records

GET  /courses/{course_id}/coursework
     - List coursework with video links
```

**Authentication:** Requires cookies.json to exist.

---

### Downloads Endpoints (`/downloads`)

**Router:** `app/api/routers/downloads.py`

```
POST /downloads?user_id={user_id}&course_id={course_id}
     Body: {"video_link_ids": [1, 2, 3]}
     - Create download jobs for specified videos
     - Jobs start as PENDING and worker picks them up

GET  /downloads?user_id={user_id}
     - List all download jobs for user
     - Includes status, progress, errors

GET  /downloads/{job_id}
     - Get detailed job status with video/course info

DELETE /downloads/{job_id}
     - Cancel a download job (sets status to CANCELLED)
```

**Flow:**
1. Client calls POST /downloads with video IDs
2. API creates DownloadJob records (status=PENDING)
3. Worker picks up jobs and updates status (DOWNLOADING → COMPLETED/FAILED)
4. Client polls GET /downloads/{job_id} for progress

---

### Auth Endpoints (`/auth`) - **DISABLED**

**Router:** `app/api/routers/auth.py` (commented out in `app/main.py:68`)

OAuth2 flow endpoints (not currently used):
- `GET /auth/url` - Generate OAuth2 authorization URL
- `GET /auth/callback` - OAuth2 callback handler
- `GET /auth/status/{user_id}` - Check credential status

**Why Disabled:** Switched to cookie-based auth for simplicity. OAuth2 code remains for future use.

---

## Background Worker System

### DownloadWorker (`app/workers/download_worker.py`)

**Purpose:** Process download jobs asynchronously.

**Lifecycle:**
1. Started in `app/main.py:lifespan` on application startup
2. Polls database every `WORKER_POLL_INTERVAL_SECONDS` (default: 5s)
3. Fetches pending jobs up to `MAX_CONCURRENT_DOWNLOADS` (default: 5)
4. Processes jobs concurrently using asyncio tasks
5. Stops gracefully on application shutdown

**Job Processing Flow:**
```
1. Fetch job from database (status=PENDING)
2. Update status → DOWNLOADING
3. Call VideoDownloaderService.download_video()
4. Update progress in database (via callback)
5. On success:
   - Update status → COMPLETED
   - Set output_path, file_size_bytes
   - Mark VideoLink.is_downloaded = True
6. On failure:
   - Increment retry_count
   - If retry_count < MAX_RETRIES:
       - Reset status → PENDING (will retry)
   - Else:
       - Update status → FAILED
       - Set error_message
```

**Concurrency Control:**
- `self.current_jobs` set tracks jobs being processed
- Won't pick up jobs already in progress
- Respects `MAX_CONCURRENT_DOWNLOADS` limit

**Retry Logic:**
- Max retries: `WORKER_MAX_RETRIES` (default: 3)
- Retry on transient yt-dlp errors
- Exponential backoff in `VideoDownloaderService`

**⚠️ Limitation:** Single worker instance. See `PLANO_MELHORIAS.md` for multi-worker plan.

---

## Development Workflows

### Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd classroom-downloader-api

# 2. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install FFmpeg (system dependency)
sudo apt-get install ffmpeg  # Debian/Ubuntu
brew install ffmpeg          # macOS

# 5. Configure environment
cp .env.example .env
# Edit .env with your settings

# 6. Setup database
alembic upgrade head

# 7. Import Google cookies
python import_cookies.py
# Follow prompts to import cookies from browser export

# 8. Run application
uvicorn app.main:app --reload
```

---

### Database Migrations

**Create Migration:**
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add new field"

# Review generated migration in migrations/versions/
# Edit if needed

# Apply migration
alembic upgrade head
```

**Rollback:**
```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

**Migration Best Practices:**
- Always review auto-generated migrations
- Test migrations on dev database first
- Never edit applied migrations (create new ones)
- Include both `upgrade()` and `downgrade()` functions

---

### Running the Application

**Development:**
```bash
# With auto-reload
uvicorn app.main:app --reload --port 8001

# With debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

**Production:**
```bash
# Via Docker
docker build -t classroom-api .
docker run -p 8001:8001 --env-file .env classroom-api

# Via uvicorn (production settings)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

**Worker Management:**
- Worker starts automatically with app (integrated in lifespan)
- No separate worker process needed
- Check worker logs for job processing activity

---

### Testing (Planned)

**Current State:** Test structure exists but NO tests implemented.

**Planned Test Structure:**
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── services/
│   │   ├── test_video_downloader.py
│   │   └── test_google_classroom.py
│   └── repositories/
│       ├── test_course_repository.py
│       └── test_download_repository.py
└── integration/
    ├── test_courses_router.py
    └── test_downloads_router.py
```

**Run Tests (when implemented):**
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

**See:** `PLANO_MELHORIAS.md` for detailed testing roadmap.

---

## Code Conventions

### Python Style

**Formatting:**
- **Line length:** 100 characters (not enforced yet, but recommended)
- **Quotes:** Double quotes preferred
- **Imports:** Organize by standard library → third-party → local

**Type Hints:**
- Use type hints for all function signatures
- Use `Optional[T]` for nullable types
- Use `list[T]` / `dict[K, V]` (modern syntax)

**Async/Await:**
- All database operations are async
- All HTTP calls are async
- Use `asyncio.create_task()` for background tasks
- Avoid blocking operations in async functions

---

### Naming Conventions

**Files & Modules:**
- `snake_case.py` for all Python files
- `__init__.py` for package initialization

**Classes:**
- `PascalCase` for classes
- Repository: `<Entity>Repository`
- Service: `<Feature>Service`
- Schema: `<Entity>Response`, `<Entity>Create`, `<Entity>Update`

**Functions & Methods:**
- `snake_case` for functions/methods
- Prefix with `_` for private methods
- Async functions: no special prefix, just use `async def`

**Database Models:**
- Singular names: `User`, `Course`, `DownloadJob`
- Table names: plural (`users`, `courses`, `download_jobs`)

---

### Error Handling

**Repositories:**
- Return `None` for not found (don't raise)
- Let database exceptions bubble up

**Services:**
- Catch specific exceptions
- Log errors with context
- Return error tuples: `(success: bool, result: Optional[T], error: Optional[str])`

**Routers:**
- Raise `HTTPException` for client errors (4xx)
- Let unhandled exceptions become 500 errors
- Use FastAPI dependency injection for validation

**Example:**
```python
# Service
async def download_video(url: str) -> tuple[bool, Optional[Path], Optional[str]]:
    try:
        result = await self._download(url)
        return True, result.path, None
    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        return False, None, str(e)

# Router
@router.post("/downloads")
async def create_download(request: DownloadRequest):
    if not request.video_link_ids:
        raise HTTPException(400, "No video IDs provided")

    # Process...
```

---

### Logging

**Current State:** Standard Python `logging` module.

**Log Levels:**
- `DEBUG` - Detailed diagnostic info (progress updates, etc.)
- `INFO` - General informational messages (job started/completed)
- `WARNING` - Warnings (retries, non-critical errors)
- `ERROR` - Errors (download failures, exceptions)

**Log Context:**
```python
logger.info(f"Download started: job_id={job_id}, url={url}")
logger.error(f"Download failed: {error}", exc_info=True)
```

**Future:** Migrate to `structlog` for structured logging (see `PLANO_MELHORIAS.md`).

---

### Configuration

**Pattern:** Pydantic Settings (`app/core/config.py`)

**Environment Variables:**
- All config loaded from `.env` file
- Type validation via Pydantic
- Use `get_settings()` function (cached)

**Adding New Settings:**
```python
# app/core/config.py
class Settings(BaseSettings):
    # Add new field
    new_feature_enabled: bool = Field(default=False)

# .env
NEW_FEATURE_ENABLED=true

# Usage
settings = get_settings()
if settings.new_feature_enabled:
    # ...
```

---

## Common Tasks

### Adding a New Endpoint

**1. Create Schema (if needed):**
```python
# app/schemas/new_feature.py
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    field1: str
    field2: int

class NewFeatureResponse(BaseModel):
    id: int
    result: str
```

**2. Add Repository Method (if needed):**
```python
# app/repositories/new_repository.py
class NewRepository(BaseRepository[NewModel]):
    async def get_by_field(self, value: str) -> list[NewModel]:
        result = await self.db.execute(
            select(NewModel).where(NewModel.field == value)
        )
        return list(result.scalars().all())
```

**3. Create Service (if complex logic):**
```python
# app/services/new_service.py
class NewService:
    async def process(self, data: NewFeatureRequest) -> NewFeatureResponse:
        # Business logic here
        return NewFeatureResponse(...)
```

**4. Add Router Endpoint:**
```python
# app/api/routers/new_router.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # Implementation
    return response
```

**5. Register Router in `main.py`:**
```python
# app/main.py
from app.api.routers import new_router

def create_app():
    app = FastAPI(...)
    app.include_router(new_router.router)
    return app
```

---

### Adding a New Database Model

**1. Define Model:**
```python
# app/domain/models.py
class NewModel(Base):
    __tablename__ = "new_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent_table.id"))
    parent: Mapped["ParentModel"] = relationship("ParentModel", back_populates="children")
```

**2. Create Migration:**
```bash
alembic revision --autogenerate -m "Add new_table"
```

**3. Review & Apply:**
```bash
# Check generated migration
cat migrations/versions/<revision>_add_new_table.py

# Apply
alembic upgrade head
```

**4. Create Repository:**
```python
# app/repositories/new_repository.py
class NewRepository(BaseRepository[NewModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(NewModel, db)
```

---

### Debugging Download Issues

**1. Check Worker Logs:**
```bash
# Look for worker errors
grep "worker" logs/app.log
grep "Download" logs/app.log
```

**2. Check Job Status:**
```python
# Direct database query
SELECT id, status, error_message, retry_count
FROM download_jobs
WHERE status = 'failed'
ORDER BY created_at DESC;
```

**3. Test yt-dlp Manually:**
```bash
# Test if yt-dlp can download
yt-dlp "https://drive.google.com/..." \
    --cookies cookies.json \
    --format "bestvideo+bestaudio/best"
```

**4. Check Cookies:**
```bash
# Verify cookies exist
python check_cookies.py

# Re-import if needed
python import_cookies.py
```

**5. Check Disk Space:**
```bash
df -h /app/downloads
```

---

### Cookie Troubleshooting

**Symptoms:**
- 401/403 errors when syncing courses
- "cookies not found" errors
- Google Drive downloads fail

**Solutions:**

**1. Check Cookie File:**
```bash
# Should exist and contain SID, HSID, etc.
cat cookies.json
```

**2. Re-export from Browser:**
```
1. Install "Get cookies.txt LOCALLY" extension
2. Navigate to classroom.google.com
3. Click extension → Export cookies.txt
4. Run: python import_cookies.py
5. Paste cookies and confirm
```

**3. Verify Cookie Format:**
```json
{
    "SID": "g.a000...",
    "HSID": "A...",
    "SSID": "A...",
    "APISID": "...",
    "SAPISID": "..."
}
```

**4. Check Expiration:**
- Google cookies typically last 1-2 weeks
- Re-export if older than 2 weeks
- No automatic refresh mechanism yet

---

## Important Context & Gotchas

### 1. Authentication Architecture

**Current State:**
- ✅ **Cookie-based auth** (via `cookies.json`) - ACTIVE
- ❌ **OAuth2 flow** (via `auth.py`) - DISABLED

**Why Cookies?**
- Simpler for single-user deployment
- No OAuth2 consent screen needed
- Works with existing Google session

**Drawbacks:**
- Manual cookie export/import
- Cookies expire (need re-export)
- Not scalable to multi-user

**Migration Path:**
- OAuth2 code exists and is functional
- Uncomment `app/main.py:68` to enable
- Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Delete `cookies.json`

**Router Selection:**
```python
# app/main.py
# Current (cookies):
app.include_router(courses_simple.router)

# To enable OAuth2:
# app.include_router(auth.router)
# app.include_router(courses.router)  # OAuth2 version
# Comment out courses_simple
```

---

### 2. User Model Not Used

**Important:** The `User` model exists but is **NOT actively used** in cookie-based auth.

**Why It Exists:**
- Originally designed for OAuth2 flow
- Stores encrypted OAuth2 tokens
- Preserved for future OAuth2 migration

**Current Flow:**
- Endpoints accept `user_id` as query param
- **No validation** that user_id exists
- No authentication/authorization

**Implications:**
- Anyone can pass any `user_id`
- No user isolation in single-user deployment
- Need to add proper auth before multi-user

---

### 3. Worker Concurrency

**Current Limitation:**
- Single worker instance
- Max 5 concurrent downloads (`MAX_CONCURRENT_DOWNLOADS`)
- No distributed worker support

**Why Single Worker?**
- Simplified development
- No job locking needed
- Sufficient for personal use

**Scaling Issues:**
- Multiple API instances would spawn duplicate workers
- Jobs could be picked up twice
- Need distributed locking (Redis, PostgreSQL advisory locks)

**Solution (Planned):**
- See `PLANO_MELHORIAS.md` Section 4.1
- Use PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED`
- Add `worker_id` to track ownership
- Support multiple worker instances

---

### 4. No CORS Configuration

**Current State:**
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ INSECURE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security Risk:**
- Allows requests from ANY origin
- Credentials exposed to malicious sites

**Fix Before Production:**
```python
origins = ["http://localhost:3000"]  # Your frontend URL
if settings.environment == "production":
    origins = ["https://yourdomain.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    ...
)
```

---

### 5. Cookie Storage Security

**⚠️ CRITICAL ISSUE:**

Cookies stored in plaintext: `cookies.json`

**Risk:**
- `SID`, `SAPISID` are session tokens
- Anyone with access to `cookies.json` can impersonate user
- No encryption at rest

**Mitigation Plan:**
```python
# Planned (from PLANO_MELHORIAS.md)
class CookieManager:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    def save_cookies(self, cookies: dict) -> None:
        encrypted = self.cipher.encrypt(json.dumps(cookies).encode())
        self.cookies_file.write_bytes(encrypted)
```

**See:** `PLANO_MELHORIAS.md` Section 1.4 for full implementation.

---

### 6. Video Link Extraction

**Important:** Video extraction is **heuristic-based**, not perfect.

**Supported Sources:**
- YouTube (`youtube.com/watch`, `youtu.be/`)
- Google Drive (`drive.google.com/file/d/`, `/open?id=`)
- Vimeo (`vimeo.com/`)

**Extraction Points:**
- Coursework `description` (HTML)
- `materials` array (attachments)
- `driveFile` objects

**Limitations:**
- Embedded iframes not parsed
- Links in PDFs not extracted
- Some URL formats missed

**Code:** `app/services/google_classroom_simple.py:_extract_video_links_from_text()`

**Improving Extraction:**
1. Add regex patterns for new sources
2. Parse HTML with BeautifulSoup
3. Extract from linked documents (PDFs)

---

### 7. Database Connection Pooling

**Configuration:**
```python
# app/db/database.py
engine = create_async_engine(
    settings.database_url,
    pool_size=5,           # Max persistent connections
    max_overflow=10,       # Max temporary connections
    pool_pre_ping=True,    # Verify connections before use
)
```

**Pool Exhaustion:**
- Symptom: "QueuePool limit exceeded"
- Cause: Sessions not closed properly
- Fix: Always use `async with get_db_context()`

**Monitoring:**
```python
# Check pool stats
print(engine.pool.status())
```

---

### 8. yt-dlp and FFmpeg

**Important:** Both required for video downloads.

**yt-dlp:**
- Python library (installed via pip)
- Supports 1000+ sites including Google Drive
- Handles DASH/HLS streams

**FFmpeg:**
- System binary (not Python package)
- Required for merging video+audio
- Must be in PATH

**Installation:**
```bash
# Debian/Ubuntu
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

**Docker:**
- Dockerfile already includes FFmpeg
- No manual installation needed

---

### 9. Alembic Gotchas

**Auto-generation Issues:**

**Problem:** Alembic doesn't detect changes sometimes.

**Solutions:**
```bash
# Force detection
alembic revision --autogenerate -m "Change" --head head

# Manual migration if auto-gen fails
alembic revision -m "Manual change"
# Edit migrations/versions/<id>_manual_change.py manually
```

**Import Errors:**

**Problem:** "No module named 'app'" in migrations.

**Solution:**
```python
# migrations/env.py
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**Multiple Heads:**

**Problem:** "Multiple heads detected."

**Solution:**
```bash
# Merge branches
alembic merge heads -m "Merge migrations"
```

---

### 10. Async Context Managers

**Pattern:** Always use `async with` for database sessions.

**❌ Wrong:**
```python
db = async_session()
result = await db.execute(...)
await db.close()  # Might not run if exception
```

**✅ Correct:**
```python
async with get_db_context() as db:
    result = await db.execute(...)
    # Automatically closed even on exception
```

**In Workers:**
```python
# Create new session for each job
async def process_job(job_id: int):
    async with get_db_context() as db:
        # Process job
        pass
```

---

## Future Improvements

### High Priority (Phase 1 - Foundation)

**From `PLANO_MELHORIAS.md`:**

1. **Testing Infrastructure** 🔴 CRITICAL
   - 0% coverage currently
   - Need: unit tests, integration tests, fixtures
   - Target: 70%+ coverage
   - See: Section 1.1

2. **Code Quality Tools** 🟡 IMPORTANT
   - Setup: Black, Ruff, MyPy, pre-commit hooks
   - CI/CD: GitHub Actions
   - See: Section 1.2

3. **Structured Logging** 🟡 IMPORTANT
   - Migrate to structlog
   - Redact sensitive data (cookies, tokens)
   - JSON format for production
   - See: Section 1.3

4. **Security Hardening** 🔴 CRITICAL
   - Encrypt cookies at rest
   - Fix CORS configuration
   - Add rate limiting
   - Admin token authentication
   - See: Section 1.4

---

### Medium Priority (Phase 2 - Architecture)

5. **Domain-Driven Design Refactor** 🟡 IMPORTANT
   - Break large services into smaller components
   - Add value objects
   - Implement orchestrators
   - See: Section 2.1

6. **Factory Pattern** 🟢 DESIRABLE
   - Centralize entity creation logic
   - See: Section 2.2

7. **Enhanced Repositories** 🟡 IMPORTANT
   - Add specialized query methods
   - Implement pessimistic locking for workers
   - Eager loading to prevent N+1 queries
   - See: Section 2.3

---

### Lower Priority (Phase 3-4)

8. **Observability**
   - Prometheus metrics
   - Grafana dashboards
   - Advanced health checks
   - See: Sections 3.1-3.2

9. **Scalability**
   - Multi-worker support
   - Redis caching
   - Database query optimization
   - Incremental downloads (checksum verification)
   - See: Sections 4.1-4.4

---

### Completed Features ✅

- ✅ Basic FastAPI application structure
- ✅ SQLAlchemy 2.0 async ORM
- ✅ Google Classroom API integration
- ✅ yt-dlp video downloading
- ✅ Background worker system
- ✅ Docker containerization
- ✅ Database migrations with Alembic
- ✅ Cookie-based authentication
- ✅ Progress tracking for downloads
- ✅ Retry logic for failed downloads

---

## Quick Reference

### Key Files Cheat Sheet

| File | Purpose | When to Edit |
|------|---------|--------------|
| `app/main.py` | App factory & lifespan | Adding routers, middleware |
| `app/core/config.py` | Settings | Adding config variables |
| `app/domain/models.py` | Database models | Adding tables/columns |
| `app/api/routers/` | API endpoints | Adding/modifying endpoints |
| `app/services/` | Business logic | Complex operations |
| `app/repositories/` | Database queries | Data access patterns |
| `app/workers/download_worker.py` | Background jobs | Worker behavior |
| `.env` | Configuration | Environment-specific settings |
| `requirements.txt` | Dependencies | Adding packages |
| `Dockerfile` | Container setup | Deployment changes |

---

### Common Commands

```bash
# Development
uvicorn app.main:app --reload

# Database
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1

# Testing (when implemented)
pytest
pytest --cov=app

# Docker
docker build -t classroom-api .
docker run -p 8001:8001 --env-file .env classroom-api

# Utilities
python import_cookies.py      # Import cookies
python check_cookies.py        # Verify cookies
python generate_encryption_key.py  # Generate Fernet key
```

---

### Environment Variables Quick Reference

```bash
# Application
APP_NAME=Classroom Downloader API
DEBUG=False
HOST=0.0.0.0
PORT=8001

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/classroom

# Google (OAuth2 - optional)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Security
ENCRYPTION_KEY=xxx  # Fernet key

# Downloads
DOWNLOAD_DIR=/app/downloads
MAX_CONCURRENT_DOWNLOADS=5
WORKER_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
```

---

## Support & Resources

### Documentation
- **README.md** - User-facing setup guide
- **PLANO_MELHORIAS.md** - Detailed improvement roadmap (Portuguese)
- **CLAUDE.md** - This file (AI assistant guide)

### External Resources
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Google Classroom API](https://developers.google.com/classroom)

### Getting Help
- Check logs in `logs/` directory
- Review error messages in FastAPI `/docs` interface
- Use `--debug` flag for detailed output
- Consult `PLANO_MELHORIAS.md` for known issues

---

**Last Updated:** 2025-12-01
**Maintainer:** See repository contributors
**License:** MIT
