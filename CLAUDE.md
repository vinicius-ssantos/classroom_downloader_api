# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Classroom Downloader API** is a FastAPI microservice for automated video downloads from Google Classroom. It uses cookie-based authentication (simplified mode) or OAuth2, async/await throughout, and a PostgreSQL-backed job queue with background workers.

## Quick Start Commands

```bash
# Setup (first time)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Cookie-based auth (simplified, no OAuth2 needed)
python import_cookies.py  # Import cookies from requests_classrom.txt and requests_drive.txt

# Database migrations
alembic upgrade head  # Apply all migrations
alembic downgrade -1  # Rollback one migration
alembic revision --autogenerate -m "description"  # Generate new migration

# Run API
uvicorn app.main:app --reload  # Development (auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8001  # Production

# Testing (note: test suite is minimal, needs expansion)
pytest  # Run all tests
pytest --cov=app tests/  # With coverage
pytest tests/unit/  # Unit tests only
pytest tests/integration/  # Integration tests only

# Code quality (not yet configured, see PLANO_MELHORIAS.md)
black app/  # Format code
ruff check app/  # Lint
mypy app/  # Type checking
```

## Architecture Overview

### Layered Architecture Pattern

```
┌─────────────────────────────────────────┐
│  FastAPI Routers (app/api/routers/)    │  ← HTTP endpoints
├─────────────────────────────────────────┤
│  Services (app/services/)               │  ← Business logic
├─────────────────────────────────────────┤
│  Repositories (app/repositories/)       │  ← Data access
├─────────────────────────────────────────┤
│  SQLAlchemy Models (app/domain/models)  │  ← ORM entities
├─────────────────────────────────────────┤
│  PostgreSQL / SQLite                    │  ← Database
└─────────────────────────────────────────┘

Background: DownloadWorker (app/workers/) polls DB for PENDING jobs
```

### Key Architectural Decisions

**Authentication Modes:**
- **Cookie-based (active)**: Extracts Google session cookies from browser DevTools via `import_cookies.py`. Cookies stored in `.secrets/cookies.json` (not encrypted). Simple but expires ~1 hour. Used by `GoogleClassroomSimpleService` and `GoogleHTTPClient`.
- **OAuth2 (commented out)**: Full OAuth2 flow with encrypted token storage. Router exists (`app/api/routers/auth.py`) but disabled in `app/main.py:68`. Use for production.

**Database Sessions:**
- All database access is async via `AsyncSession`
- Use `Depends(get_db)` in routers for automatic session management (commit/rollback)
- Use `get_db_context()` context manager in workers/services for manual control
- Engine configured in `app/db/database.py` with connection pooling (pool_size=5, max_overflow=10)

**Background Worker:**
- Single worker instance (`DownloadWorker`) started in `app/main.py` lifespan
- Polls database every 5 seconds for `PENDING` jobs (configurable: `WORKER_POLL_INTERVAL_SECONDS`)
- Max concurrent downloads: 5 (configurable: `MAX_CONCURRENT_DOWNLOADS`)
- Jobs tracked in `DownloadJob` table with status: PENDING → DOWNLOADING → COMPLETED/FAILED/CANCELLED
- Worker shutdown: `stop()` sets flag, then `cancel()` task (abrupt, no graceful drain - see PLANO_MELHORIAS.md Phase 3.3)

**Video Download Flow:**
1. User syncs courses: `POST /courses/sync` → `GoogleClassroomSimpleService.sync_courses()`
2. User syncs coursework: `POST /courses/{id}/sync-coursework` → extracts video links from materials
3. User enqueues downloads: `POST /downloads` → creates `DownloadJob` records (status=PENDING)
4. Background worker polls, picks up jobs, updates status=DOWNLOADING
5. `VideoDownloaderService` uses `yt-dlp` with cookies to download from Google Drive
6. yt-dlp calls FFmpeg to merge DASH streams (video.mp4 + audio.m4a → final.mp4)
7. Progress tracked via `DownloadProgress` callbacks, updated in DB
8. Final status: COMPLETED (with file_path) or FAILED (with error_message)

**File Organization:**
- Downloaded videos: `downloads/{course_name}/{sanitized_filename}.mp4`
- Cookies: `.secrets/cookies.json` (plain JSON, should encrypt - see security notes)
- Logs: stdout (not file-based yet, see PLANO_MELHORIAS.md Phase 1.3)

## Critical Implementation Notes

### Database Models Relationships

```python
User (1) ──< (N) Course
         ──< (N) DownloadJob

Course (1) ──< (N) Coursework
           ──< (N) DownloadJob

Coursework (1) ──< (N) VideoLink

VideoLink (1) ──< (N) DownloadJob
```

All foreign keys use SQLAlchemy relationships with `cascade="all, delete-orphan"` except DownloadJob (no cascade from VideoLink to preserve history).

### Service Layer Pattern

**Two parallel service implementations exist (technical debt):**

1. **OAuth2 version (unused):**
   - `app/services/google_classroom.py` - Uses OAuth2 credentials
   - `app/services/google_auth.py` - Manages OAuth2 flow
   - `app/services/credentials_manager.py` - Fernet encryption

2. **Cookie version (active):**
   - `app/services/google_classroom_simple.py` - Uses cookies
   - `app/services/cookie_manager.py` - Parses cURL files
   - `app/services/http_client.py` - Adds cookies to requests

When modifying Google Classroom integration, only update the `*_simple.py` versions unless re-enabling OAuth2.

### Repository Pattern

All repositories extend `BaseRepository[T]` with generic CRUD:
```python
async def get(id: int) -> T | None
async def get_all(skip: int = 0, limit: int = 100) -> list[T]
async def add(entity: T) -> T
async def update(entity: T) -> T
async def delete(id: int) -> bool
```

Specialized repositories add domain-specific queries:
- `DownloadJobRepository.get_by_status(status: DownloadStatus)` - Filter by job status
- `VideoLinkRepository.get_by_coursework(coursework_id: int)` - Get videos for material
- `CourseRepository.get_by_user(user_id: int)` - User's courses

**Important:** No pessimistic locking implemented yet. Multi-worker deployments will have race conditions (see PLANO_MELHORIAS.md Phase 4.1).

### Configuration Management

Settings in `app/core/config.py` use Pydantic BaseSettings:
- Environment variables override `.env` file
- `@lru_cache()` on `get_settings()` means settings are loaded once and cached
- Restart required for config changes (no hot reload)

**Required settings for cookie-based mode:**
```env
DATABASE_URL=sqlite+aiosqlite:///./classroom.db  # Or postgresql+asyncpg://...
DOWNLOAD_DIR=./downloads
MAX_CONCURRENT_DOWNLOADS=5
WORKER_POLL_INTERVAL_SECONDS=5
WORKER_MAX_RETRIES=3
LOG_LEVEL=INFO
```

**Optional (OAuth2 only, currently unused):**
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ENCRYPTION_KEY=...
```

### Video Download Implementation

**yt-dlp Integration:**
- Configured in `app/services/video_downloader.py`
- Supports Google Drive DASH streams (separate video/audio tracks)
- FFmpeg required for merging (install: `apt-get install ffmpeg` / `brew install ffmpeg`)
- Progress tracking via yt-dlp hooks: `downloading`, `finished`, `error`
- Retry logic: 3 attempts with exponential backoff (via `tenacity` library)

**Progress Callback Flow:**
```python
# Worker calls downloader with callback
async def progress_callback(progress: DownloadProgress):
    job.progress_percent = progress.percent
    job.downloaded_bytes = progress.downloaded_bytes
    await db.commit()

await video_downloader.download_video(
    url=video_link.url,
    output_path=output_path,
    progress_callback=progress_callback,
)
```

Frontend can poll `GET /downloads/{job_id}` to show real-time progress.

## Common Development Patterns

### Adding a New API Endpoint

1. Create Pydantic schemas in `app/schemas/`:
   ```python
   class MyRequest(BaseModel):
       field: str

   class MyResponse(BaseModel):
       result: str

       model_config = ConfigDict(from_attributes=True)
   ```

2. Add router in `app/api/routers/`:
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.db.database import get_db

   router = APIRouter(prefix="/my-endpoint", tags=["my-feature"])

   @router.post("", response_model=MyResponse)
   async def my_endpoint(
       request: MyRequest,
       db: AsyncSession = Depends(get_db),
   ):
       # Business logic
       return MyResponse(result="success")
   ```

3. Register in `app/main.py`:
   ```python
   from app.api.routers import my_router
   app.include_router(my_router.router)
   ```

### Adding a Database Model

1. Define model in `app/domain/models.py`:
   ```python
   class MyModel(Base):
       __tablename__ = "my_table"

       id: Mapped[int] = mapped_column(primary_key=True)
       name: Mapped[str] = mapped_column(String(255))
       created_at: Mapped[datetime] = mapped_column(
           DateTime(timezone=True),
           server_default=func.now(),
       )
   ```

2. Create migration:
   ```bash
   alembic revision --autogenerate -m "Add my_table"
   ```

3. Review and edit migration in `migrations/versions/`, then:
   ```bash
   alembic upgrade head
   ```

### Adding a Repository

1. Create repository in `app/repositories/`:
   ```python
   from app.repositories.base import BaseRepository
   from app.domain.models import MyModel

   class MyRepository(BaseRepository[MyModel]):
       def __init__(self, session: AsyncSession):
           super().__init__(session, MyModel)

       async def custom_query(self, param: str) -> list[MyModel]:
           stmt = select(MyModel).where(MyModel.name == param)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```

2. Use in services/routers:
   ```python
   async def my_service(db: AsyncSession):
       repo = MyRepository(db)
       results = await repo.custom_query("value")
   ```

## Known Issues and Limitations

**Critical (blocks production):**
- No multi-user cookie support: single cookie set shared by all users (hardcoded `user_id=1`)
- Cookies expire ~1 hour, no automatic refresh
- No graceful worker shutdown: `cancel()` interrupts downloads mid-flight
- Zero test coverage (test structure exists but empty)

**High priority (see PLANO_MELHORIAS.md):**
- CORS configured as `allow_origins=["*"]` (app/main.py:59)
- No rate limiting on endpoints
- No input validation beyond Pydantic schemas (no authorization checks)
- Cookies stored in plain JSON (should encrypt)
- OAuth2 implementation exists but disabled (dead code)

**Technical debt:**
- Two parallel service implementations (OAuth2 vs cookie-based)
- No structured logging (uses basic `logging` module)
- No metrics/observability (Prometheus recommended)
- No pessimistic locking for multi-worker scenarios
- Hardcoded User-Agent in HTTPClient will become outdated

**Performance:**
- N+1 query issues in some endpoints (needs eager loading with `selectinload`)
- No database indexes beyond primary keys and foreign keys
- No caching layer (Redis recommended for course metadata)

## Important Files to Check

When making changes, always review:
- `app/main.py` - Application factory, router registration, lifespan management
- `app/core/config.py` - Configuration schema and defaults
- `app/db/database.py` - Database engine and session management
- `app/domain/models.py` - All ORM models and relationships
- `.env.example` - Required environment variables (copy to `.env`)
- `PLANO_MELHORIAS.md` - Comprehensive improvement plan with 4 phases

## Testing Strategy

Current state: **Minimal (0% coverage)**

Test structure exists but not implemented:
```
tests/
├── conftest.py (empty)
├── unit/ (empty)
└── integration/ (empty)
```

When writing tests, follow patterns from `FastAPI_HeroSpark_MyEdools_Impacta` reference project (see PLANO_MELHORIAS.md Phase 1.1 for detailed examples):

1. Use `pytest-asyncio` for async tests
2. Create fixtures in `conftest.py` for:
   - In-memory database (`sqlite+aiosqlite:///:memory:`)
   - Test client with dependency overrides
   - Mock cookies and credentials
3. Test repositories with real database (integration)
4. Test services with mocked repositories (unit)
5. Test routers with TestClient (integration)

## Reference Documentation

- **SETUP_SIMPLES.md** - Cookie-based setup (no OAuth2)
- **GETTING_STARTED.md** - Full OAuth2 setup
- **COMO_USAR.md** - User guide with API workflow
- **ANALISE_REQUESTS.md** - Technical analysis of Google Classroom/Drive APIs
- **PLANO_MELHORIAS.md** - 4-phase improvement roadmap (200-280h effort)
- **Swagger UI** - http://localhost:8001/docs (interactive API documentation)

## Docker Usage

```bash
# Development (with docker-compose from parent directory)
cd ..
docker-compose up --build

# The compose file mounts:
# - ./classroom-downloader-api:/app (code hot reload)
# - ./classroom-downloader-api/.secrets:/app/.secrets (cookies persist)
# - classroom_downloads:/app/downloads (downloaded files persist)

# Services:
# - db: PostgreSQL 16 (shared with other services)
# - classroom-downloader-api: This API (port 8001)
```

**Important:** Before running docker-compose, import cookies locally first:
```bash
cd classroom-downloader-api
python import_cookies.py
```

The `.secrets/cookies.json` will be mounted into the container.

## Migration from OAuth2 to Cookie-based Auth

If re-enabling OAuth2 (production deployment):

1. Uncomment `app/api/routers/auth.py` import in `app/main.py:68`
2. Configure Google Cloud Console (see GETTING_STARTED.md steps 4-7)
3. Generate encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
4. Set environment variables:
   ```env
   GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-secret
   ENCRYPTION_KEY=your-fernet-key
   ```
5. Update services to use `GoogleClassroomService` instead of `GoogleClassroomSimpleService`
6. Test OAuth2 flow: `GET /auth/url` → authorize → `GET /auth/callback`

Note: This will require database schema changes to support per-user credentials (see PLANO_MELHORIAS.md Phase 1.4).
