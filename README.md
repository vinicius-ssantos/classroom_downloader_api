# Classroom Downloader API

Microserviço para download automatizado de vídeos do Google Classroom.

## 📋 Análise de Viabilidade

✅ **CONFIRMADO:** É possível fazer download das aulas! Veja [ANALISE_REQUESTS.md](./ANALISE_REQUESTS.md) para detalhes técnicos.

## 🎯 Funcionalidades

- 🔐 **Autenticação OAuth2** com Google
- 📚 **Descoberta de Cursos** via Google Classroom API
- 📥 **Download de Vídeos** do Google Drive (formato DASH)
- ⚡ **Workers Assíncronos** para downloads paralelos
- 📊 **Tracking de Progresso** em tempo real
- 🔄 **Retry Automático** em caso de falha

## 🏗️ Arquitetura

```
classroom-downloader-api/
├── app/
│   ├── api/routers/          # FastAPI endpoints
│   ├── core/                 # Config, logging, security
│   ├── db/                   # Models, database setup
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic
│   │   ├── google_classroom.py
│   │   ├── google_auth.py
│   │   └── video_downloader.py
│   ├── domain/               # Value objects
│   ├── schemas/              # Pydantic schemas
│   └── workers/              # Background workers
├── migrations/               # Alembic migrations
├── tests/                    # Unit + Integration tests
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🚀 Quickstart

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 16
- FFmpeg (for video merging)

### 2. Installation

```bash
# Clone
git clone <repo>
cd classroom-downloader-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg
sudo apt-get install ffmpeg  # Linux
# brew install ffmpeg        # Mac
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Google OAuth2 Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable APIs:
   - Google Classroom API
   - Google Drive API
4. Create OAuth2 Credentials
5. Set redirect URI: `http://localhost:8001/auth/callback`
6. Copy Client ID and Secret to `.env`

**Generate Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Database Setup

```bash
# Run migrations
alembic upgrade head
```

### 5. Run

```bash
# API
uvicorn app.main:app --reload

# Worker (in another terminal)
python -m app.workers.download_worker
```

### 6. API Documentation

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

## 🐳 Docker

```bash
# Build and run
docker-compose up --build

# API will be available at http://localhost:8001
```

## 📚 Stack

- **Framework:** FastAPI 0.121+
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0 (async)
- **Download:** yt-dlp (suporta Google Drive)
- **Auth:** Google OAuth2
- **Queue:** PostgreSQL-based

## 🔧 Development

```bash
# Run tests
pytest

# Coverage
pytest --cov=app tests/

# Lint
ruff check app/
black app/

# Type check
mypy app/
```

## 📖 API Endpoints

### Authentication
- `GET /auth/login` - Inicia fluxo OAuth2
- `GET /auth/callback` - Callback OAuth2

### Courses
- `GET /courses` - Lista cursos
- `GET /courses/{course_id}` - Detalhes do curso
- `GET /courses/{course_id}/coursework` - Lista materiais

### Downloads
- `POST /downloads` - Enfileira download
- `GET /downloads/{download_id}` - Status do download
- `GET /downloads` - Lista downloads
- `DELETE /downloads/{download_id}` - Cancela download

### Batch
- `POST /courses/{course_id}/download-all` - Download de curso completo
- `GET /batch-downloads/{job_id}` - Status do batch

### Health
- `GET /health` - Health check
- `GET /metrics` - Métricas Prometheus

## 🔐 Security

- ✅ OAuth2 tokens criptografados em repouso
- ✅ Logs com redação de dados sensíveis
- ✅ Validação de inputs com Pydantic
- ✅ HTTPS em produção

## ⚠️ Limitações

1. **Quotas do Google Classroom API:** 10,000 requests/day
2. **Tamanho dos vídeos:** Vídeos grandes (1-2 GB) demoram
3. **Expiração de tokens:** Links expiram em ~1h
4. **Compliance:** Usar apenas para conteúdo autorizado

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.
