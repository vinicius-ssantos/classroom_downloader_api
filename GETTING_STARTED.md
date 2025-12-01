# 🚀 Primeiros Passos

Guia rápido para começar a usar o Classroom Downloader API em **5 minutos**!

## ✅ Pré-requisitos

- [ ] Python 3.11+ instalado
- [ ] PostgreSQL instalado e rodando
- [ ] Git Bash ou terminal Windows

## 📝 Passo a Passo

### 1️⃣ Ativar Ambiente Virtual

```bash
cd D:\Users\vinic\PycharmProjects\classroom-downloader-api
.venv\Scripts\activate
```

### 2️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

**Tempo estimado:** 2-3 minutos

### 3️⃣ Configurar Automaticamente

```bash
python setup.py
```

Este script vai:
- ✅ Gerar chave de criptografia
- ✅ Atualizar o arquivo .env
- ✅ Criar diretório de downloads
- ✅ Verificar configurações

### 4️⃣ Configurar Google OAuth2

**IMPORTANTE:** Você precisa fazer isso antes de usar a API!

1. Acesse: https://console.cloud.google.com

2. Crie um novo projeto (ex: "Classroom Downloader")

3. No menu lateral, vá em **APIs e Serviços** → **Biblioteca**

4. Habilite estas APIs:
   - ✅ Google Classroom API
   - ✅ Google Drive API

5. Vá em **Credenciais** → **Criar Credenciais** → **ID do cliente OAuth**

6. Configure a tela de consentimento OAuth:
   - Tipo: Externo
   - Nome: "Classroom Downloader"
   - Email de suporte: seu email
   - Adicione escopos:
     - `/auth/classroom.courses.readonly`
     - `/auth/classroom.coursework.students.readonly`
     - `/auth/drive.readonly`

7. Criar credenciais OAuth2:
   - Tipo de aplicativo: **Aplicativo da Web**
   - Nome: "Classroom Downloader"
   - URIs de redirecionamento autorizados:
     ```
     http://localhost:8001/auth/callback
     ```

8. Copie o **Client ID** e **Client Secret**

9. Abra o arquivo `.env` e cole:
   ```
   GOOGLE_CLIENT_ID=seu-client-id-aqui.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=seu-client-secret-aqui
   ```

### 5️⃣ Configurar PostgreSQL

Opção A - PostgreSQL Local (padrão):
```bash
# Criar banco de dados
createdb classroom

# Se precisar de usuário/senha diferentes, edite DATABASE_URL no .env
```

Opção B - Usar SQLite (mais simples para testes):
```bash
# Edite .env e mude:
DATABASE_URL=sqlite+aiosqlite:///./classroom.db
```

### 6️⃣ Criar Tabelas do Banco

```bash
alembic upgrade head
```

Você deve ver:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial database schema
```

### 7️⃣ Iniciar a API

```bash
uvicorn app.main:app --reload
```

Você deve ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 8️⃣ Testar

Abra no navegador: **http://localhost:8001/docs**

Você verá a documentação interativa Swagger UI!

## 🎯 Primeiro Teste

### Teste 1: Health Check

No navegador ou terminal:
```bash
curl http://localhost:8001/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "service": "Classroom Downloader API",
  "version": "1.0.0"
}
```

### Teste 2: Autenticação

1. Acesse http://localhost:8001/docs
2. Expanda **GET /auth/url**
3. Clique em **Try it out** → **Execute**
4. Copie a `auth_url` da resposta
5. Abra a URL no navegador
6. Faça login com sua conta Google
7. Autorize o aplicativo
8. Você será redirecionado e verá seu `user_id`

**Guarde este `user_id`!** Você vai usá-lo em todas as requisições.

## 📚 Próximos Passos

Agora que está tudo rodando, veja:
- **USAGE.md** - Guia completo de como usar a API
- **http://localhost:8001/docs** - Documentação interativa

## 🆘 Problemas Comuns

### Erro: "ModuleNotFoundError"
```bash
# Certifique-se que o venv está ativado
.venv\Scripts\activate
pip install -r requirements.txt
```

### Erro: "connection refused" (PostgreSQL)
```bash
# Verifique se PostgreSQL está rodando
# Windows: Services → PostgreSQL
# Ou use SQLite (veja passo 5)
```

### Erro: "No credentials found"
- Você precisa fazer o fluxo de autenticação OAuth2 primeiro (Teste 2)

### Erro: "Invalid encryption key"
```bash
# Gere uma nova chave
python generate_encryption_key.py
# Copie para o .env
```

## ✅ Checklist Final

- [ ] Python e PostgreSQL instalados
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` configurado
- [ ] Google OAuth2 configurado
- [ ] Banco de dados criado
- [ ] Migrations executadas (`alembic upgrade head`)
- [ ] API rodando (`uvicorn app.main:app --reload`)
- [ ] Health check funcionando
- [ ] Autenticação testada

## 🎉 Pronto!

Agora você pode:
1. Sincronizar seus cursos do Google Classroom
2. Extrair links de vídeos automaticamente
3. Baixar vídeos em segundo plano
4. Monitorar o progresso em tempo real

Divirta-se! 🚀
