# 📋 Plano de Melhorias - Classroom Downloader API

> Baseado na análise comparativa com **FastAPI_HeroSpark_MyEdools_Impacta**

**Data:** 2025-12-01
**Status Atual:** MVP Funcional (uso pessoal/desenvolvimento)
**Meta:** Aplicação Production-Ready com qualidade enterprise

---

## 📊 Resumo Executivo

### Análise Comparativa

| Aspecto | HeroSpark (Referência) | Classroom API (Atual) | Gap |
|---------|----------------------|---------------------|-----|
| **Linhas de Código** | 6,025 | ~2,500 | ⚠️ Menos robusto |
| **Arquivos Python** | 95+ | ~40 | ⚠️ Menos modular |
| **Cobertura de Testes** | ~80% | 0% | 🔴 Crítico |
| **Repositórios** | 10+ especializados | 5 básicos | ⚠️ Incompleto |
| **Serviços** | 35+ (DDD) | 6 | ⚠️ Precisa refatorar |
| **Documentação** | 52KB+ (ADRs, guias) | 20KB (básico) | ⚠️ Expandir |
| **Workers** | Multi-worker com locks | Single worker | ⚠️ Escalabilidade |
| **Autenticação** | Token-based + Encrypted | Cookies manuais | 🔴 Crítico |
| **Observabilidade** | Logs estruturados + Metrics | Logs básicos | 🔴 Produção |
| **CI/CD** | GitHub Actions + Pre-commit | Nenhum | 🔴 Qualidade |

---

## 🎯 Roadmap de Melhorias

### Fase 1: Fundação e Qualidade (2-3 semanas)
**Objetivo:** Tornar o código testável e seguro

### Fase 2: Arquitetura e Padrões (3-4 semanas)
**Objetivo:** Alinhar com padrões enterprise do HeroSpark

### Fase 3: Produção e Observabilidade (2-3 semanas)
**Objetivo:** Pronto para deploy em produção

### Fase 4: Escalabilidade e Performance (3-4 semanas)
**Objetivo:** Suportar múltiplos usuários e alta carga

---

# FASE 1: FUNDAÇÃO E QUALIDADE

## 1.1 Testes Automatizados 🔴 CRÍTICO

### Problema Atual
- **0% de cobertura de testes**
- Nenhum teste implementado (apenas estrutura de diretórios)
- Impossível refatorar com segurança
- Bugs descobertos apenas em produção

### Solução Inspirada no HeroSpark

**1. Criar conftest.py com fixtures compartilhadas**

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient
from app.main import create_app
from app.core.config import Settings

@pytest.fixture
async def test_settings():
    """Test-specific settings"""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        debug=True,
        log_level="DEBUG",
        encryption_key="test-key-32-bytes-long-exactly!!",
    )

@pytest.fixture
async def async_engine(test_settings):
    """In-memory database engine"""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(async_engine):
    """Database session for tests"""
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(test_settings):
    """HTTP test client"""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_cookies():
    """Sample Google cookies for testing"""
    return {
        "SID": "test_sid_value",
        "HSID": "test_hsid_value",
        "SSID": "test_ssid_value",
        "APISID": "test_apisid_value",
        "SAPISID": "test_sapisid_value",
    }
```

**2. Implementar testes de integração para routers**

```python
# tests/integration/test_courses_router.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_list_courses_empty(client: AsyncClient):
    response = await client.get("/courses?user_id=1")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.integration
async def test_sync_courses_missing_cookies(client: AsyncClient):
    response = await client.post("/courses/sync?user_id=1")
    assert response.status_code == 401
    assert "cookies" in response.json()["detail"].lower()

@pytest.mark.integration
async def test_download_flow_end_to_end(
    client: AsyncClient,
    db_session,
    mock_cookies,
):
    # 1. Sync courses (mocked)
    # 2. Get course details
    # 3. Sync coursework
    # 4. Create download job
    # 5. Verify job status
    pass
```

**3. Testes unitários para serviços**

```python
# tests/unit/services/test_video_downloader.py
import pytest
from app.services.video_downloader import VideoDownloaderService

@pytest.mark.unit
async def test_download_with_progress_callback(tmp_path, mock_cookies):
    service = VideoDownloaderService(download_dir=str(tmp_path))

    progress_updates = []
    async def progress_cb(progress):
        progress_updates.append(progress.percent)

    # Mock yt-dlp to simulate download
    with patch('yt_dlp.YoutubeDL') as mock_ytdl:
        await service.download_video(
            url="https://example.com/video",
            output_path=str(tmp_path / "video.mp4"),
            progress_callback=progress_cb,
        )

    assert len(progress_updates) > 0
    assert progress_updates[-1] == 100.0
```

**4. Testes para repositories**

```python
# tests/unit/repositories/test_download_repository.py
import pytest
from app.repositories.download_job_repository import DownloadJobRepository
from app.domain.models import DownloadJob, DownloadStatus

@pytest.mark.unit
async def test_get_pending_jobs(db_session):
    repo = DownloadJobRepository(db_session)

    # Create test data
    job1 = DownloadJob(user_id=1, status=DownloadStatus.PENDING)
    job2 = DownloadJob(user_id=1, status=DownloadStatus.COMPLETED)
    db_session.add_all([job1, job2])
    await db_session.commit()

    # Query
    pending = await repo.get_pending_jobs(limit=10)

    assert len(pending) == 1
    assert pending[0].status == DownloadStatus.PENDING
```

### Entregáveis
- [ ] `tests/conftest.py` com 10+ fixtures
- [ ] `tests/integration/` com 15+ testes (routers)
- [ ] `tests/unit/services/` com 20+ testes
- [ ] `tests/unit/repositories/` com 15+ testes
- [ ] Cobertura: **0% → 70%+**
- [ ] CI/CD: GitHub Actions rodando testes

### Métricas de Sucesso
- ✅ `pytest --cov=app` passa com 70%+
- ✅ Todos os endpoints têm pelo menos 1 teste
- ✅ CI falha se cobertura < 70%

---

## 1.2 Qualidade de Código e Linting 🟡 IMPORTANTE

### Problema Atual
- Sem formatação automática
- Sem linting ou análise estática
- Sem verificação de tipos
- Inconsistências de estilo

### Solução Inspirada no HeroSpark

**1. Configurar pyproject.toml**

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
    "N",   # pep8-naming
    "S",   # bandit (security)
    "RUF", # ruff-specific rules
]
ignore = [
    "S101",  # assert usage (OK in tests)
    "B008",  # function calls in argument defaults (FastAPI Depends)
]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]
addopts = [
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=70",
]
```

**2. Pre-commit hooks**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy, types-requests]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile, black]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: [-r, app]
```

**3. CI/CD Pipeline**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run Black
        run: black --check app/ tests/

      - name: Run Ruff
        run: ruff check app/ tests/

      - name: Run MyPy
        run: mypy app/

      - name: Run Tests
        run: pytest --cov=app --cov-fail-under=70

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit
        run: bandit -r app/

      - name: Run Safety
        run: safety check
```

### Entregáveis
- [ ] `pyproject.toml` configurado
- [ ] `.pre-commit-config.yaml` com 6+ hooks
- [ ] `.github/workflows/ci.yml` funcionando
- [ ] `requirements-dev.txt` com ferramentas de dev
- [ ] Código formatado com Black (100% compliance)
- [ ] Tipos anotados em 100% das funções públicas

### Métricas de Sucesso
- ✅ `black --check .` passa
- ✅ `ruff check .` passa
- ✅ `mypy app/` passa sem erros
- ✅ CI verde em todos os PRs

---

## 1.3 Logging Estruturado e Redação 🟡 IMPORTANTE

### Problema Atual
- Logs básicos com `logging` padrão
- Sem redação de dados sensíveis
- Headers e cookies aparecem em logs
- Formato texto dificulta parsing

### Solução Inspirada no HeroSpark

**1. Implementar logger estruturado**

```python
# app/core/logging.py
import structlog
import logging
import sys
from typing import Any

def configure_logging(log_level: str = "INFO", log_format: str = "text"):
    """Configure structured logging"""

    # Processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        redact_sensitive_data,  # Custom processor
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

def redact_sensitive_data(logger, method_name, event_dict):
    """Redact sensitive fields from logs"""
    sensitive_patterns = [
        r"(Authorization:\s*Bearer\s+)([^\s]+)",
        r"(cookie:\s*)([^\n]+)",
        r"(SID|HSID|SSID|APISID|SAPISID)=([^;]+)",
        r"(encryption_key:\s*)([^\s]+)",
    ]

    message = event_dict.get("event", "")
    for pattern in sensitive_patterns:
        message = re.sub(pattern, r"\1***REDACTED***", message, flags=re.IGNORECASE)
    event_dict["event"] = message

    return event_dict

# Usage
logger = structlog.get_logger(__name__)
logger.info("download_started", lesson_id=123, user_id=1, url="https://...")
```

**2. Atualizar serviços para usar logging estruturado**

```python
# app/services/video_downloader.py (refatorado)
import structlog

logger = structlog.get_logger(__name__)

class VideoDownloaderService:
    async def download_video(self, url: str, output_path: str):
        logger.info(
            "download_started",
            url=url,
            output_path=output_path,
        )

        try:
            result = await self._download_with_ytdlp(url, output_path)
            logger.info(
                "download_completed",
                url=url,
                file_size=result.file_size,
                duration_seconds=result.duration,
            )
            return result
        except Exception as e:
            logger.error(
                "download_failed",
                url=url,
                error=str(e),
                exc_info=True,
            )
            raise
```

**3. Redação em middlewares**

```python
# app/api/middleware/logging.py
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Redact sensitive headers
        safe_headers = {
            k: v if k.lower() not in {"authorization", "cookie"}
            else "***REDACTED***"
            for k, v in request.headers.items()
        }

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            headers=safe_headers,
        )

        response = await call_next(request)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response
```

### Entregáveis
- [ ] `app/core/logging.py` implementado
- [ ] Todos os serviços usando `structlog`
- [ ] Middleware de logging de requests
- [ ] Redação de: Authorization, Cookie, SID, HSID, SSID, APISID, SAPISID
- [ ] Configuração de formato JSON para produção
- [ ] Documentação de campos de log

### Métricas de Sucesso
- ✅ 0 logs com cookies/tokens visíveis
- ✅ Logs parseáveis com `jq` em JSON mode
- ✅ Rastreabilidade: request_id em todos os logs

---

## 1.4 Segurança Básica 🔴 CRÍTICO

### Problema Atual
- CORS com `allow_origins=["*"]`
- Cookies em arquivo JSON não criptografado
- Sem rate limiting
- Sem validação de user_id nos endpoints
- Sem HTTPS enforcement

### Solução Inspirada no HeroSpark

**1. Configurar CORS corretamente**

```python
# app/main.py (atualizar create_app)
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(...)

    # CORS configurável por ambiente
    origins = settings.backend_cors_origins or []
    if settings.environment == "development":
        origins = ["http://localhost:3000", "http://localhost:8001"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
```

**2. Adicionar admin token authentication**

```python
# app/api/security.py
from fastapi import HTTPException, Request, Depends
from app.core.config import Settings, get_settings

def require_admin_token(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Require admin token for sensitive operations"""
    expected_token = settings.admin_api_token
    if not expected_token:
        return  # No token configured, allow (dev mode)

    provided_token = request.headers.get("x-admin-token")
    if provided_token != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin token",
        )

# Usage in routers
@router.post("/downloads")
async def create_download(
    request: DownloadRequest,
    _: None = Depends(require_admin_token),  # Protect endpoint
):
    ...
```

**3. Criptografar cookies em repouso**

```python
# app/services/cookie_manager.py (atualizar)
from cryptography.fernet import Fernet
import json

class CookieManager:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    def save_cookies(self, cookies: dict[str, str]) -> None:
        """Save encrypted cookies"""
        plaintext = json.dumps(cookies).encode()
        encrypted = self.cipher.encrypt(plaintext)
        self.cookies_file.write_bytes(encrypted)

    def load_cookies(self) -> dict[str, str]:
        """Load and decrypt cookies"""
        if not self.cookies_file.exists():
            return {}
        encrypted = self.cookies_file.read_bytes()
        plaintext = self.cipher.decrypt(encrypted)
        return json.loads(plaintext)
```

**4. Rate limiting**

```python
# app/api/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# In create_app()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In routers
@router.post("/downloads")
@limiter.limit("10/minute")  # Max 10 downloads per minute
async def create_download(request: Request, ...):
    ...
```

**5. HTTPS redirect em produção**

```python
# app/main.py
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(...)

    if settings.force_https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)
```

### Entregáveis
- [ ] CORS configurado por ambiente
- [ ] Admin token authentication implementado
- [ ] Cookies criptografados com Fernet
- [ ] Rate limiting em endpoints críticos
- [ ] HTTPS redirect em produção
- [ ] Security headers (CSP, X-Frame-Options, etc.)
- [ ] Auditoria de segurança documentada

### Métricas de Sucesso
- ✅ Bandit scan sem alertas críticos
- ✅ Cookies não legíveis sem chave
- ✅ Rate limit bloqueia após threshold
- ✅ CORS rejeitada de origens não autorizadas

---

# FASE 2: ARQUITETURA E PADRÕES

## 2.1 Refatorar para Domain-Driven Design 🟡 IMPORTANTE

### Problema Atual
- Serviços grandes e monolíticos
- Lógica de negócio espalhada
- Sem value objects
- Acoplamento entre camadas

### Solução Inspirada no HeroSpark

**1. Criar Value Objects**

```python
# app/domain/value_objects.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class GoogleCookieSet:
    """Immutable set of Google authentication cookies"""
    sid: str
    hsid: str
    ssid: str
    apisid: str
    sapisid: str
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def to_cookie_dict(self) -> dict[str, str]:
        return {
            "SID": self.sid,
            "HSID": self.hsid,
            "SSID": self.ssid,
            "APISID": self.apisid,
            "SAPISID": self.sapisid,
        }

@dataclass(frozen=True)
class VideoSource:
    """Represents a downloadable video source"""
    url: str
    format: str  # "hls", "mp4", "dash"
    quality: Optional[str] = None  # "720p", "1080p"
    bandwidth: Optional[int] = None

    def is_high_quality(self) -> bool:
        return self.quality in {"1080p", "1440p", "2160p"}

@dataclass(frozen=True)
class DownloadProgress:
    """Immutable download progress snapshot"""
    job_id: int
    percent: float
    downloaded_bytes: int
    total_bytes: int
    speed_mbps: float

    def is_complete(self) -> bool:
        return self.percent >= 100.0
```

**2. Dividir serviços grandes em componentes menores**

```python
# app/services/downloads/preflight.py
"""Pre-download validation"""

class DownloadPreflightService:
    async def validate_download_request(
        self,
        user_id: int,
        video_link_id: int,
    ) -> DownloadPlan:
        """Validate all preconditions before download"""

        # 1. Check cookies exist and are valid
        cookies = await self._validate_cookies()

        # 2. Check video link exists
        video_link = await self._validate_video_link(video_link_id)

        # 3. Check disk space
        await self._validate_disk_space(video_link.estimated_size)

        # 4. Scan for existing artifacts
        existing_file = await self._check_existing_file(video_link)

        return DownloadPlan(
            video_link=video_link,
            cookies=cookies,
            skip_download=existing_file is not None,
            output_path=self._compute_output_path(video_link),
        )
```

```python
# app/services/downloads/runner.py
"""Execute download operations"""

class DownloadRunner:
    async def execute_download(
        self,
        plan: DownloadPlan,
        progress_callback: Optional[Callable] = None,
    ) -> DownloadResult:
        """Execute download with progress tracking"""

        if plan.skip_download:
            return DownloadResult.skipped(plan.output_path)

        try:
            result = await self._download_with_ytdlp(
                url=plan.video_link.url,
                output_path=plan.output_path,
                cookies=plan.cookies.to_cookie_dict(),
                progress_callback=progress_callback,
            )
            return DownloadResult.success(result)
        except Exception as e:
            logger.error("download_failed", error=str(e), exc_info=True)
            return DownloadResult.failed(str(e))
```

**3. Criar Orchestrator de alto nível**

```python
# app/services/downloads/orchestrator.py
"""High-level download orchestration"""

class DownloadOrchestrator:
    def __init__(
        self,
        session: AsyncSession,
        preflight: DownloadPreflightService,
        runner: DownloadRunner,
    ):
        self.session = session
        self.preflight = preflight
        self.runner = runner

    async def enqueue_download(
        self,
        user_id: int,
        video_link_id: int,
    ) -> DownloadJob:
        """Enqueue a download job after validation"""

        # Preflight checks
        plan = await self.preflight.validate_download_request(
            user_id, video_link_id
        )

        # Create job
        job = DownloadJob(
            user_id=user_id,
            video_link_id=video_link_id,
            status=DownloadStatus.QUEUED,
            output_path=plan.output_path,
        )
        self.session.add(job)
        await self.session.commit()

        return job
```

### Entregáveis
- [ ] `app/domain/value_objects.py` com 5+ value objects
- [ ] Refatorar `VideoDownloaderService` em 3 componentes:
  - `DownloadPreflightService`
  - `DownloadRunner`
  - `DownloadOrchestrator`
- [ ] Refatorar `GoogleClassroomSimpleService` em:
  - `CourseDiscoveryService`
  - `CourseworkSyncService`
  - `VideoExtractionService`
- [ ] Documentar arquitetura em ADR

### Métricas de Sucesso
- ✅ Nenhum serviço > 300 linhas
- ✅ Cada serviço tem responsabilidade única
- ✅ Value objects imutáveis e testáveis

---

## 2.2 Factory Pattern para Entidades Complexas 🟢 DESEJÁVEL

### Problema Atual
- Criação de entidades espalhada no código
- Lógica de defaults duplicada
- Difícil garantir consistência

### Solução Inspirada no HeroSpark

```python
# app/factories/download_job_factory.py
from datetime import datetime
from app.domain.models import DownloadJob, DownloadStatus

class DownloadJobFactory:
    @staticmethod
    def create_queued(
        user_id: int,
        video_link_id: int,
        output_path: str,
    ) -> DownloadJob:
        """Create a new queued download job"""
        return DownloadJob(
            user_id=user_id,
            video_link_id=video_link_id,
            status=DownloadStatus.QUEUED,
            output_path=output_path,
            progress_percent=0.0,
            retry_count=0,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def create_from_existing_file(
        user_id: int,
        video_link_id: int,
        file_path: str,
        file_size: int,
        checksum: str,
    ) -> DownloadJob:
        """Create a completed job for an existing file"""
        return DownloadJob(
            user_id=user_id,
            video_link_id=video_link_id,
            status=DownloadStatus.COMPLETED,
            output_path=file_path,
            progress_percent=100.0,
            downloaded_bytes=file_size,
            total_bytes=file_size,
            file_checksum=checksum,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )
```

### Entregáveis
- [ ] `app/factories/download_job_factory.py`
- [ ] `app/factories/course_factory.py`
- [ ] `app/factories/video_link_factory.py`
- [ ] Testes para cada factory

---

## 2.3 Melhorar Repositories 🟡 IMPORTANTE

### Problema Atual
- Repositories básicos (apenas CRUD)
- Queries complexas nos serviços
- Sem query builders especializados
- Sem pessimistic locking para workers

### Solução Inspirada no HeroSpark

**1. Adicionar métodos especializados**

```python
# app/repositories/download_job_repository.py
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

class DownloadJobRepository(BaseRepository[DownloadJob]):
    async def get_pending_jobs(
        self,
        limit: int = 10,
    ) -> list[DownloadJob]:
        """Get pending jobs ordered by priority"""
        stmt = (
            select(DownloadJob)
            .where(DownloadJob.status == DownloadStatus.PENDING)
            .order_by(DownloadJob.created_at.asc())
            .limit(limit)
            .options(selectinload(DownloadJob.video_link))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def acquire_next_queued_job(
        self,
        worker_id: str,
    ) -> Optional[DownloadJob]:
        """Acquire next job with pessimistic lock"""
        stmt = (
            select(DownloadJob)
            .where(DownloadJob.status == DownloadStatus.QUEUED)
            .order_by(DownloadJob.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)  # Pessimistic lock
        )
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()

        if job:
            job.status = DownloadStatus.RUNNING
            job.worker_id = worker_id
            job.started_at = datetime.utcnow()
            await self.session.commit()

        return job

    async def get_jobs_by_status(
        self,
        status: DownloadStatus,
        limit: int = 50,
    ) -> list[DownloadJob]:
        """Filter jobs by status"""
        stmt = (
            select(DownloadJob)
            .where(DownloadJob.status == status)
            .order_by(DownloadJob.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

**2. Adicionar repository para video links**

```python
# app/repositories/video_link_repository.py
class VideoLinkRepository(BaseRepository[VideoLink]):
    async def get_downloadable_links(
        self,
        course_id: int,
    ) -> list[VideoLink]:
        """Get all video links for a course that haven't been downloaded"""
        stmt = (
            select(VideoLink)
            .join(VideoLink.coursework)
            .where(
                Coursework.course_id == course_id,
                VideoLink.is_downloaded == False,
            )
            .options(selectinload(VideoLink.coursework))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_downloaded(
        self,
        video_link_id: int,
        download_path: str,
    ) -> None:
        """Mark video link as downloaded"""
        stmt = (
            update(VideoLink)
            .where(VideoLink.id == video_link_id)
            .values(
                is_downloaded=True,
                download_path=download_path,
                updated_at=datetime.utcnow(),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
```

### Entregáveis
- [ ] Adicionar 5+ métodos especializados em cada repository
- [ ] Implementar pessimistic locking em `acquire_next_queued_job`
- [ ] Eager loading com `selectinload` em queries N+1
- [ ] Testes para todas as queries complexas

---

# FASE 3: PRODUÇÃO E OBSERVABILIDADE

## 3.1 Prometheus Metrics 🟡 IMPORTANTE

### Problema Atual
- Sem métricas de performance
- Impossível monitorar saúde do sistema
- Sem alertas automáticos

### Solução Inspirada no HeroSpark

```python
# app/api/routers/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
download_jobs_total = Counter(
    "download_jobs_total",
    "Total download jobs created",
    ["status"],
)

download_duration_seconds = Histogram(
    "download_duration_seconds",
    "Download duration in seconds",
    ["quality"],
)

download_bytes_total = Counter(
    "download_bytes_total",
    "Total bytes downloaded",
)

active_downloads_gauge = Gauge(
    "active_downloads",
    "Number of currently active downloads",
)

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )
```

**Instrumentar serviços:**

```python
# app/services/downloads/runner.py
import time

class DownloadRunner:
    async def execute_download(self, plan: DownloadPlan):
        download_jobs_total.labels(status="started").inc()
        active_downloads_gauge.inc()

        start_time = time.time()
        try:
            result = await self._download_with_ytdlp(...)

            duration = time.time() - start_time
            download_duration_seconds.labels(quality=plan.quality).observe(duration)
            download_bytes_total.inc(result.file_size)
            download_jobs_total.labels(status="completed").inc()

            return result
        except Exception as e:
            download_jobs_total.labels(status="failed").inc()
            raise
        finally:
            active_downloads_gauge.dec()
```

### Entregáveis
- [ ] `/metrics` endpoint implementado
- [ ] 10+ métricas exportadas (counters, histograms, gauges)
- [ ] Grafana dashboard configurado
- [ ] Alertas configurados (jobs falhando > 50%)

---

## 3.2 Health Checks Avançados 🟡 IMPORTANTE

### Problema Atual
- Health check básico (apenas retorna 200)
- Sem verificação de dependências
- Sem readiness vs liveness

### Solução Inspirada no HeroSpark

```python
# app/api/routers/health.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", status_code=status.HTTP_200_OK)
async def health():
    """Liveness probe - is the app running?"""
    return {"status": "ok", "timestamp": datetime.utcnow()}

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness(
    session: AsyncSession = Depends(get_db_session),
):
    """Readiness probe - can the app serve traffic?"""
    checks = {}

    # Check database
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Check cookies
    try:
        cookie_manager = get_cookie_manager()
        cookies = cookie_manager.load_cookies()
        checks["cookies"] = "ok" if cookies else "missing"
    except Exception as e:
        checks["cookies"] = f"error: {str(e)}"

    # Check worker
    try:
        worker = get_download_worker()
        checks["worker"] = "running" if worker.is_running else "stopped"
    except Exception as e:
        checks["worker"] = f"error: {str(e)}"

    # Overall status
    all_ok = all(v == "ok" or v == "running" for v in checks.values())
    status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ok else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow(),
        },
    )
```

### Entregáveis
- [ ] `/health` (liveness)
- [ ] `/health/ready` (readiness)
- [ ] Verificações de: database, cookies, worker, disk space
- [ ] Kubernetes manifests com probes configuradas

---

## 3.3 Graceful Shutdown 🟡 IMPORTANTE

### Problema Atual
- `worker_task.cancel()` é abrupto
- Downloads podem ser interrompidos
- Dados podem ser corrompidos

### Solução Inspirada no HeroSpark

```python
# app/workers/download_worker.py
import asyncio
from asyncio import Event

class DownloadWorker:
    def __init__(self):
        self._shutdown_event = Event()
        self._current_jobs: set[int] = set()

    async def start(self) -> None:
        """Start worker loop"""
        logger.info("worker_started", worker_id=self.worker_id)

        while not self._shutdown_event.is_set():
            try:
                processed = await self._process_once()
                if not processed:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error("worker_error", error=str(e), exc_info=True)
                await asyncio.sleep(self.poll_interval)

        # Wait for current jobs to finish
        logger.info("worker_draining", active_jobs=len(self._current_jobs))
        while self._current_jobs:
            await asyncio.sleep(1)

        logger.info("worker_stopped", worker_id=self.worker_id)

    async def stop(self) -> None:
        """Gracefully stop worker"""
        logger.info("worker_shutdown_requested", worker_id=self.worker_id)
        self._shutdown_event.set()
```

**Lifespan atualizado:**

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    worker = get_download_worker()
    worker_task = asyncio.create_task(worker.start())

    yield

    # Shutdown
    logger.info("app_shutdown_started")
    await worker.stop()  # Signal shutdown
    await asyncio.wait_for(worker_task, timeout=30.0)  # Wait up to 30s
    await close_db()
    logger.info("app_shutdown_completed")
```

### Entregáveis
- [ ] Worker com graceful shutdown implementado
- [ ] Timeout configurável (30s default)
- [ ] Jobs em progresso completam antes de shutdown
- [ ] Logs de shutdown detalhados

---

# FASE 4: ESCALABILIDADE E PERFORMANCE

## 4.1 Multi-Worker Support 🟡 IMPORTANTE

### Problema Atual
- Apenas 1 worker em execução
- Não escala horizontalmente
- Sem worker coordination

### Solução Inspirada no HeroSpark

```python
# app/workers/factory.py
from app.workers.download_worker import DownloadWorker

def create_download_workers(
    session_factory,
    settings: Settings,
) -> list[DownloadWorker]:
    """Create multiple worker instances"""
    workers = []
    for i in range(settings.max_download_workers):
        worker = DownloadWorker(
            worker_id=f"worker-{i}",
            session_factory=session_factory,
            poll_interval=settings.worker_poll_interval_seconds,
            max_retries=settings.worker_max_retries,
        )
        workers.append(worker)
    return workers

# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    workers = []
    if settings.download_worker_enabled:
        workers = create_download_workers(
            get_async_session_factory(),
            settings,
        )
        for worker in workers:
            asyncio.create_task(worker.start())

    yield

    # Shutdown
    for worker in workers:
        await worker.stop()
```

**Worker coordination com pessimistic locking:**

```python
# app/repositories/download_job_repository.py
async def acquire_next_queued_job(
    self,
    worker_id: str,
) -> Optional[DownloadJob]:
    """Acquire next job with database-level locking"""
    stmt = (
        select(DownloadJob)
        .where(DownloadJob.status == DownloadStatus.QUEUED)
        .order_by(DownloadJob.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)  # Skip locked rows
    )
    result = await self.session.execute(stmt)
    job = result.scalar_one_or_none()

    if job:
        job.status = DownloadStatus.RUNNING
        job.worker_id = worker_id
        job.picked_at = datetime.utcnow()
        await self.session.commit()

    return job
```

### Entregáveis
- [ ] `create_download_workers()` factory
- [ ] Configuração `MAX_DOWNLOAD_WORKERS` (default: 4)
- [ ] Pessimistic locking com `skip_locked=True`
- [ ] Worker health tracking (heartbeat)
- [ ] Stale job detection e requeue

---

## 4.2 Incremental Downloads (Checksum Verification) 🟢 DESEJÁVEL

### Problema Atual
- Sempre re-baixa arquivos completos
- Desperdício de banda e tempo
- Sem verificação de integridade

### Solução Inspirada no HeroSpark

```python
# app/services/downloads/artifact_scanner.py
import hashlib
from pathlib import Path

class DownloadArtifactScanner:
    async def scan_existing_files(
        self,
        video_link_ids: list[int],
    ) -> dict[int, ArtifactReport]:
        """Scan filesystem for existing downloads"""
        reports = {}

        for video_link_id in video_link_ids:
            video_link = await self._repo.get(video_link_id)
            if not video_link:
                continue

            file_path = Path(video_link.download_path)
            if not file_path.exists():
                reports[video_link_id] = ArtifactReport(
                    exists=False,
                    checksum=None,
                )
                continue

            # Calculate SHA256
            checksum = await self._calculate_checksum(file_path)

            # Check against DB
            job = await self._find_completed_job(video_link_id, checksum)

            reports[video_link_id] = ArtifactReport(
                exists=True,
                checksum=checksum,
                valid=job is not None,
                file_size=file_path.stat().st_size,
            )

        return reports

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
```

**Usar scanner antes de downloads:**

```python
# app/services/downloads/orchestrator.py
class DownloadOrchestrator:
    async def enqueue_batch_download(
        self,
        video_link_ids: list[int],
        force_refresh: bool = False,
    ) -> list[DownloadJob]:
        """Enqueue downloads with artifact scanning"""

        if not force_refresh:
            # Scan for existing files
            scanner = DownloadArtifactScanner(self.session)
            reports = await scanner.scan_existing_files(video_link_ids)

            # Filter out valid existing files
            video_link_ids = [
                vid for vid in video_link_ids
                if not reports.get(vid, {}).get("valid")
            ]

        # Enqueue remaining downloads
        jobs = []
        for video_link_id in video_link_ids:
            job = await self._create_job(video_link_id)
            jobs.append(job)

        return jobs
```

### Entregáveis
- [ ] `DownloadArtifactScanner` implementado
- [ ] SHA256 checksum em `DownloadJob.file_checksum`
- [ ] Skip de downloads para arquivos válidos existentes
- [ ] Parâmetro `force_refresh` para re-download

---

## 4.3 Database Query Optimization 🟢 DESEJÁVEL

### Problema Atual
- Queries N+1 em alguns endpoints
- Sem índices personalizados
- Sem query logging para debug

### Solução Inspirada no HeroSpark

**1. Adicionar índices estratégicos**

```python
# migrations/versions/002_add_indexes.py
def upgrade():
    # Índices para filtering
    op.create_index(
        "idx_download_job_status",
        "download_job",
        ["status"],
    )

    op.create_index(
        "idx_download_job_user_status",
        "download_job",
        ["user_id", "status"],
    )

    # Índice para worker queries
    op.create_index(
        "idx_download_job_worker_status",
        "download_job",
        ["worker_id", "status"],
    )

    # Índice para timestamp queries
    op.create_index(
        "idx_download_job_created",
        "download_job",
        ["created_at"],
    )
```

**2. Eager loading para evitar N+1**

```python
# app/repositories/course_repository.py
from sqlalchemy.orm import selectinload

async def get_courses_with_stats(
    self,
    user_id: int,
) -> list[Course]:
    """Get courses with eagerly loaded relationships"""
    stmt = (
        select(Course)
        .where(Course.owner_id == user_id)
        .options(
            selectinload(Course.coursework)
            .selectinload(Coursework.video_links)
        )
        .order_by(Course.updated_at.desc())
    )
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

**3. Query logging para debug**

```python
# app/db/database.py
import logging

# Enable SQLAlchemy query logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log queries in debug mode
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
```

### Entregáveis
- [ ] 5+ índices estratégicos criados
- [ ] Eager loading em endpoints de listagem
- [ ] Query logging configurável
- [ ] EXPLAIN ANALYZE para queries lentas documentado

---

## 4.4 Caching Layer (Redis) 🟢 DESEJÁVEL

### Problema Atual
- Toda requisição bate no banco
- Course metadata não muda frequentemente
- Desperdício de recursos

### Solução

```python
# app/core/cache.py
import redis.asyncio as redis
import json
from typing import Optional

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: dict,
        ttl_seconds: int = 300,
    ) -> None:
        """Set value in cache with TTL"""
        await self.redis.setex(
            key,
            ttl_seconds,
            json.dumps(value),
        )

    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        await self.redis.delete(key)

# Usage in routers
@router.get("/courses/{course_id}")
async def get_course(
    course_id: int,
    cache: CacheService = Depends(get_cache),
    session: AsyncSession = Depends(get_db_session),
):
    # Try cache first
    cache_key = f"course:{course_id}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Fetch from DB
    repo = CourseRepository(session)
    course = await repo.get(course_id)

    # Cache result
    course_dict = CourseResponse.from_orm(course).dict()
    await cache.set(cache_key, course_dict, ttl_seconds=600)

    return course_dict
```

### Entregáveis
- [ ] Redis container no docker-compose
- [ ] `CacheService` implementado
- [ ] Cache em endpoints de leitura (/courses, /coursework)
- [ ] Cache invalidation em updates

---

# ANEXOS

## Cronograma Estimado

| Fase | Duração | Esforço | Prioridade |
|------|---------|---------|------------|
| **Fase 1: Fundação** | 2-3 semanas | 40-60h | 🔴 Crítico |
| **Fase 2: Arquitetura** | 3-4 semanas | 60-80h | 🟡 Importante |
| **Fase 3: Produção** | 2-3 semanas | 40-60h | 🟡 Importante |
| **Fase 4: Escalabilidade** | 3-4 semanas | 60-80h | 🟢 Desejável |
| **Total** | **10-14 semanas** | **200-280h** | - |

## Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Cookies expiram durante refactor | Alto | Média | Implementar OAuth2 primeiro |
| Testes quebram em refatoração | Médio | Alta | Testes incrementais por módulo |
| Performance degrada com cache | Baixo | Baixa | Benchmarks antes/depois |
| Workers competem por recursos | Médio | Média | Configurar limits de concorrência |

## Dependências Novas

```txt
# Testing
pytest-mock==3.12.0
pytest-xdist==3.5.0  # Parallel test execution
faker==22.6.0

# Code Quality
black==24.3.0
ruff==0.3.0
mypy==1.9.0
pre-commit==3.6.0

# Logging
structlog==24.4.0
python-json-logger==2.0.7

# Observability
prometheus-client==0.20.0

# Security
slowapi==0.1.9  # Rate limiting

# Caching (Fase 4)
redis[asyncio]==5.0.1
```

## Referências

1. **HeroSpark Project**: `/mnt/d/Users/vinic/PycharmProjects/MyEdools_Impacta/FastAPI_HeroSpark_MyEdools_Impacta`
2. **Architecture Patterns**: [Martin Fowler - Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/)
3. **FastAPI Best Practices**: https://github.com/zhanymkanov/fastapi-best-practices
4. **12-Factor App**: https://12factor.net/
5. **Structlog Docs**: https://www.structlog.org/

---

**Próximo Passo:** Revisar e priorizar este plano com o time. Começar pela Fase 1 (Fundação).
