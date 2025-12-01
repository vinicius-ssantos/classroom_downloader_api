# 🚀 Setup Simplificado - SEM OAuth2!

Este guia mostra como usar o projeto **apenas com cookies**, sem precisar configurar Google OAuth2!

## ✅ Vantagens

- ❌ **Não precisa** criar projeto no Google Cloud Console
- ❌ **Não precisa** configurar OAuth2
- ❌ **Não precisa** ENCRYPTION_KEY
- ✅ **Só precisa** dos cookies do seu navegador!

---

## 📋 Passo a Passo

### 1. Ativar Ambiente Virtual

```bash
cd D:\Users\vinic\PycharmProjects\classroom-downloader-api
.venv\Scripts\activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Importar Cookies

Você já tem os arquivos com os cookies! Basta executar:

```bash
python import_cookies.py
```

Você vai ver algo como:

```
🍪 IMPORTAR COOKIES DO GOOGLE
====================================================================

📄 Lendo: requests_classrom.txt
   ✅ 25 cookies do Classroom
📄 Lendo: requests_drive.txt
   ✅ 23 cookies do Drive

💾 Salvando 30 cookies únicos...

✅ Cookies importados com sucesso!
📁 Salvos em: D:\...\classroom-downloader-api\.secrets\cookies.json

🔑 Cookies importantes encontrados:
   ✅ SID: g.a0002wgBc5aXFXwBg...
   ✅ HSID: AXLAYo4GEEYgJlrCJ
   ✅ SSID: AVRjWpcXZAqN4pHJS
   ✅ APISID: cqmGFqhiPsPcQHCc...
   ✅ SAPISID: bjobLAxShGMffWFa...
```

### 4. Configurar .env (Simplificado)

Edite o arquivo `.env` e **remova/comente** as linhas do OAuth2:

```env
# Application
APP_NAME=Classroom Downloader API
APP_VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8001

# Database - Use SQLite para começar rápido!
DATABASE_URL=sqlite+aiosqlite:///./classroom.db

# Downloads
DOWNLOAD_DIR=D:/Users/vinic/PycharmProjects/classroom-downloader-api/downloads
MAX_CONCURRENT_DOWNLOADS=5

# Workers
WORKER_POLL_INTERVAL_SECONDS=5
WORKER_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO

# OAuth2 - NÃO NECESSÁRIO!
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
# ENCRYPTION_KEY=...
```

### 5. Criar Banco de Dados

```bash
alembic upgrade head
```

### 6. Iniciar API

```bash
uvicorn app.main:app --reload
```

Você deve ver:

```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 7. Testar!

Abra o navegador: **http://localhost:8001/docs**

---

## 🎯 Como Usar a API

### 1. Sincronizar Cursos

```bash
POST http://localhost:8001/courses/sync?user_id=1
```

Resposta:

```json
{
  "success": true,
  "synced_count": 5,
  "total_courses": 5
}
```

### 2. Listar Cursos

```bash
GET http://localhost:8001/courses?user_id=1
```

### 3. Sincronizar Vídeos de um Curso

```bash
POST http://localhost:8001/courses/1/sync-coursework
```

### 4. Ver Vídeos Disponíveis

```bash
GET http://localhost:8001/courses/1/coursework
```

### 5. Baixar Vídeos

```bash
POST http://localhost:8001/downloads?user_id=1&course_id=1
Content-Type: application/json

{
  "video_link_ids": [1, 2, 3]
}
```

---

## 🔄 Atualizar Cookies

Seus cookies expiram eventualmente. Quando isso acontecer:

1. Acesse o Google Classroom no navegador (faça login)
2. Abra DevTools (F12)
3. Vá na aba Network
4. Copie um request como cURL
5. Cole no arquivo `requests_classrom.txt` (substitua o conteúdo)
6. Execute novamente: `python import_cookies.py`

---

## 🆘 Problemas

### Erro 401: Cookies não encontrados

```bash
python import_cookies.py
```

### Erro 403: Cookies expirados

Atualize os cookies (veja seção acima)

### Erro: Curso não encontrado

Execute sync primeiro:

```bash
POST /courses/sync?user_id=1
```

---

## 📊 Comparação

| Característica | OAuth2 | Cookies |
|----------------|--------|---------|
| Setup          | Complexo | **Simples** |
| Google Cloud   | Necessário | **Não precisa** |
| Expiração      | Refresh automático | Manual |
| Segurança      | Mais seguro | Menos seguro |
| Produção       | Recomendado | **Desenvolvimento** |

---

## ✅ Checklist

- [ ] Virtual environment ativado
- [ ] Dependências instaladas
- [ ] Cookies importados (`python import_cookies.py`)
- [ ] `.env` configurado (use SQLite!)
- [ ] Migrations executadas (`alembic upgrade head`)
- [ ] API rodando (`uvicorn app.main:app --reload`)
- [ ] Cursos sincronizados (POST /courses/sync)
- [ ] Testado no navegador (http://localhost:8001/docs)

---

## 🎉 Pronto!

Agora você pode usar a API **sem complicação de OAuth2**!

**Próximos passos:**
- Sincronize seus cursos
- Baixe alguns vídeos
- Veja USAGE.md para exemplos avançados

---

## ⚠️ Importante

**Esta abordagem é recomendada apenas para:**
- ✅ Desenvolvimento local
- ✅ Testes rápidos
- ✅ Uso pessoal

**Para produção, use OAuth2** (veja GETTING_STARTED.md)
