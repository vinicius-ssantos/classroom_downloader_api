# Guia de Uso da API

Este guia mostra como usar a Classroom Downloader API passo a passo.

## 📋 Pré-requisitos

1. API rodando: `uvicorn app.main:app --reload`
2. PostgreSQL configurado
3. Credenciais Google OAuth2 configuradas no `.env`

## 🔐 Passo 1: Autenticação

### 1.1. Obter URL de autenticação

```bash
GET http://localhost:8001/auth/url
```

**Resposta:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random_state_string"
}
```

### 1.2. Abrir URL no navegador

Abra a `auth_url` no navegador e faça login com sua conta Google.

### 1.3. Callback automático

Após autorizar, você será redirecionado para:
```
http://localhost:8001/auth/callback?code=xxx&state=xxx
```

**Resposta:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "user_id": 1,
  "user_email": "seu@email.com"
}
```

**Guarde o `user_id`** - você vai usá-lo em todas as requisições!

## 📚 Passo 2: Sincronizar Cursos

### 2.1. Buscar cursos do Google Classroom

```bash
POST http://localhost:8001/courses/sync?user_id=1
```

**Resposta:**
```json
{
  "success": true,
  "synced_count": 5,
  "total_courses": 5
}
```

### 2.2. Listar cursos sincronizados

```bash
GET http://localhost:8001/courses?user_id=1
```

**Resposta:**
```json
[
  {
    "id": 1,
    "google_course_id": "123456",
    "name": "Python Avançado",
    "state": "ACTIVE",
    "coursework_count": 0,
    "video_count": 0,
    "downloaded_count": 0
  },
  ...
]
```

## 📹 Passo 3: Sincronizar Vídeos

### 3.1. Extrair vídeos de um curso

```bash
POST http://localhost:8001/courses/1/sync-coursework?user_id=1
```

**Resposta:**
```json
{
  "success": true,
  "synced_coursework": 15,
  "new_videos": 23
}
```

### 3.2. Listar materiais com vídeos

```bash
GET http://localhost:8001/courses/1/coursework
```

**Resposta:**
```json
[
  {
    "id": 1,
    "google_coursework_id": "abc123",
    "title": "Aula 01 - Introdução",
    "description": "...",
    "work_type": "MATERIAL",
    "state": "PUBLISHED",
    "video_links": [
      {
        "id": 1,
        "url": "https://www.youtube.com/watch?v=...",
        "title": "Aula 01",
        "source_type": "youtube",
        "is_downloaded": false
      },
      {
        "id": 2,
        "url": "https://drive.google.com/file/d/.../view",
        "title": "Material Extra",
        "source_type": "drive",
        "drive_file_id": "xyz789",
        "is_downloaded": false
      }
    ]
  },
  ...
]
```

## ⬇️ Passo 4: Baixar Vídeos

### 4.1. Criar jobs de download

Pegue os `id` dos `video_links` que você quer baixar:

```bash
POST http://localhost:8001/downloads?user_id=1&course_id=1
Content-Type: application/json

{
  "video_link_ids": [1, 2, 3]
}
```

**Resposta:**
```json
{
  "created_jobs": [
    {
      "id": 1,
      "user_id": 1,
      "course_id": 1,
      "video_link_id": 1,
      "status": "PENDING",
      "progress_percent": 0,
      "created_at": "2025-12-01T15:30:00Z"
    },
    {
      "id": 2,
      "user_id": 1,
      "course_id": 1,
      "video_link_id": 2,
      "status": "PENDING",
      "progress_percent": 0,
      "created_at": "2025-12-01T15:30:01Z"
    }
  ],
  "failed_jobs": [],
  "total_requested": 3,
  "total_created": 2,
  "total_failed": 0
}
```

### 4.2. Monitorar progresso

```bash
GET http://localhost:8001/downloads/1
```

**Resposta (durante download):**
```json
{
  "id": 1,
  "status": "DOWNLOADING",
  "progress_percent": 45,
  "downloaded_bytes": 45000000,
  "total_bytes": 100000000,
  "video_url": "https://www.youtube.com/watch?v=...",
  "video_title": "Aula 01",
  "course_name": "Python Avançado",
  "coursework_title": "Aula 01 - Introdução",
  "started_at": "2025-12-01T15:30:05Z"
}
```

**Resposta (concluído):**
```json
{
  "id": 1,
  "status": "COMPLETED",
  "progress_percent": 100,
  "downloaded_bytes": 100000000,
  "total_bytes": 100000000,
  "output_path": "/app/downloads/Python_Avancado/xyz123.mp4",
  "file_size_bytes": 100000000,
  "completed_at": "2025-12-01T15:35:00Z"
}
```

### 4.3. Listar todos os downloads

```bash
GET http://localhost:8001/downloads?user_id=1
```

**Filtros disponíveis:**
- `?user_id=1` - Todos os downloads do usuário
- `?user_id=1&course_id=1` - Downloads de um curso específico
- `?user_id=1&status_filter=COMPLETED` - Filtrar por status

**Status possíveis:**
- `PENDING` - Na fila
- `DOWNLOADING` - Em progresso
- `COMPLETED` - Concluído
- `FAILED` - Falhou
- `CANCELLED` - Cancelado

### 4.4. Cancelar download

```bash
DELETE http://localhost:8001/downloads/1
```

**Resposta:**
```json
{
  "success": true,
  "message": "Download job cancelled"
}
```

## 🔍 Passo 5: Verificar Status

### 5.1. Health check

```bash
GET http://localhost:8001/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "Classroom Downloader API",
  "version": "1.0.0"
}
```

### 5.2. Verificar banco de dados

```bash
GET http://localhost:8001/health/db
```

**Resposta:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 5.3. Verificar credenciais

```bash
GET http://localhost:8001/auth/status/1
```

**Resposta:**
```json
{
  "has_credentials": true,
  "is_expired": false,
  "scopes": [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
  ]
}
```

## 🎯 Fluxo Completo (Resumo)

```bash
# 1. Autenticar
GET /auth/url
# -> Abrir URL no navegador
# -> Obter user_id do callback

# 2. Sincronizar cursos
POST /courses/sync?user_id=1

# 3. Listar cursos
GET /courses?user_id=1
# -> Pegar course_id

# 4. Sincronizar vídeos
POST /courses/1/sync-coursework?user_id=1

# 5. Ver vídeos disponíveis
GET /courses/1/coursework
# -> Pegar video_link_ids

# 6. Baixar vídeos
POST /downloads?user_id=1&course_id=1
Body: {"video_link_ids": [1, 2, 3]}

# 7. Monitorar
GET /downloads/1
```

## 📝 Notas

1. **Background Worker:** O worker processa downloads automaticamente a cada 5 segundos
2. **Downloads Paralelos:** Até 5 downloads simultâneos (configurável em `.env`)
3. **Retry:** Até 3 tentativas em caso de falha
4. **Timeout:** 1 hora por download (configurável)
5. **Formato:** Vídeos salvos como MP4 em `/app/downloads/{course_name}/`

## 🚨 Erros Comuns

### 401 Unauthorized
```json
{
  "detail": "No credentials found. Please authenticate first."
}
```
**Solução:** Execute o fluxo de autenticação novamente

### 404 Not Found
```json
{
  "detail": "Course not found"
}
```
**Solução:** Verifique se sincronizou os cursos primeiro

### 500 Internal Server Error
**Solução:** Verifique os logs do servidor para detalhes

## 📖 Documentação Interativa

Acesse http://localhost:8001/docs para testar todos os endpoints diretamente no navegador!
