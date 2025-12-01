# 🚀 Como Usar - Guia Rápido

## 📍 Localização do Projeto
```
D:\Users\vinic\PycharmProjects\MyEdools_Impacta\classroom-downloader-api
```

---

## ⚡ Opção 1: Usar Scripts Automáticos (RECOMENDADO)

### Primeira vez (Setup):
```bash
# Clique duplo no arquivo:
setup_rapido.bat
```

### Iniciar a API:
```bash
# Clique duplo no arquivo:
start_api.bat
```

---

## 🛠️ Opção 2: Comandos Manuais

### 1️⃣ Setup Inicial (primeira vez)

```bash
cd D:\Users\vinic\PycharmProjects\MyEdools_Impacta\classroom-downloader-api
.venv\Scripts\activate
pip install -r requirements.txt
python import_cookies.py
python check_cookies.py
alembic upgrade head
```

### 2️⃣ Iniciar API (sempre que quiser usar)

```bash
cd D:\Users\vinic\PycharmProjects\MyEdools_Impacta\classroom-downloader-api
.venv\Scripts\activate
uvicorn app.main:app --reload
```

### 3️⃣ Acessar

Abra no navegador: **http://localhost:8001/docs**

---

## 📚 Fluxo de Uso

### Passo 1: Sincronizar Cursos

Na interface Swagger (http://localhost:8001/docs):

1. Vá em **POST /courses/sync**
2. Clique em **Try it out**
3. Deixe `user_id = 1`
4. Clique **Execute**

Você verá quantos cursos foram sincronizados.

### Passo 2: Ver Cursos

1. Vá em **GET /courses**
2. Clique em **Try it out**
3. `user_id = 1`
4. **Execute**

Anote o `id` do curso que você quer baixar.

### Passo 3: Sincronizar Vídeos do Curso

1. Vá em **POST /courses/{course_id}/sync-coursework**
2. **Try it out**
3. Coloque o `course_id` (exemplo: `1`)
4. **Execute**

Isso vai extrair todos os vídeos do curso.

### Passo 4: Ver Vídeos Disponíveis

1. Vá em **GET /courses/{course_id}/coursework**
2. **Try it out**
3. Coloque o `course_id`
4. **Execute**

Você verá todos os materiais com seus vídeos e os `id` de cada vídeo.

### Passo 5: Baixar Vídeos

1. Vá em **POST /downloads**
2. **Try it out**
3. Preencha:
   - `user_id = 1`
   - `course_id = 1` (ou o ID do seu curso)
   - No body, coloque os IDs dos vídeos:
     ```json
     {
       "video_link_ids": [1, 2, 3]
     }
     ```
4. **Execute**

### Passo 6: Monitorar Downloads

1. Vá em **GET /downloads/{job_id}**
2. Coloque o `id` do job que você criou
3. **Execute**

Você verá o progresso: 0%, 25%, 50%, 100%...

---

## 📂 Arquivos Importantes

```
classroom-downloader-api/
├── setup_rapido.bat          ⭐ Clique para configurar
├── start_api.bat             ⭐ Clique para iniciar API
├── import_cookies.py         - Importar cookies
├── check_cookies.py          - Verificar cookies
├── requests_classrom.txt     - Seus cookies do Classroom
├── requests_drive.txt        - Seus cookies do Drive
├── .env                      - Configurações
├── classroom.db              - Banco de dados (criado automaticamente)
└── downloads/                - Vídeos baixados ficam aqui
```

---

## 🎯 Atalhos de Teclado

**No Windows Explorer:**
- Shift + Botão Direito → "Abrir janela do PowerShell aqui"
- Digite: `.\setup_rapido.bat` ou `.\start_api.bat`

---

## 🆘 Problemas Comuns

### "Ambiente virtual não encontrado"
```bash
python -m venv .venv
```

### "Cookies não encontrados"
```bash
python import_cookies.py
```

### "Porta 8001 em uso"
```bash
# Parar processos na porta 8001
netstat -ano | findstr :8001
# Anote o PID e:
taskkill /PID <numero> /F
```

### Cookies expiraram
1. Acesse Google Classroom no navegador
2. F12 → Network → Copie request como cURL
3. Cole em `requests_classrom.txt`
4. Execute: `python import_cookies.py`

---

## 📊 Status da API

### Verificar se está funcionando:
```
http://localhost:8001/health
```

### Ver documentação completa:
```
http://localhost:8001/docs
```

### Ver todos os endpoints:
```
http://localhost:8001/redoc
```

---

## 🎓 Exemplos de Uso

### Baixar curso inteiro:

1. Sincronizar curso
2. Pegar ID do curso (ex: `1`)
3. Sincronizar vídeos: `POST /courses/1/sync-coursework`
4. Ver vídeos: `GET /courses/1/coursework`
5. Copiar todos os IDs dos vídeos
6. Baixar todos: `POST /downloads` com todos os IDs

### Baixar apenas aulas específicas:

1. Ver vídeos disponíveis
2. Escolher IDs específicos (ex: aulas 1, 3, 5)
3. Baixar apenas esses: `POST /downloads` com `[1, 3, 5]`

---

## 📁 Onde ficam os vídeos?

```
D:\Users\vinic\PycharmProjects\MyEdools_Impacta\classroom-downloader-api\downloads\

└── Nome_Do_Curso\
    ├── video1.mp4
    ├── video2.mp4
    └── video3.mp4
```

---

## 🔄 Atualizar Cookies (quando expirarem)

```bash
# 1. Acesse Google Classroom no navegador
# 2. F12 → Network → Copie request como cURL
# 3. Cole em requests_classrom.txt (substitua tudo)
# 4. Execute:
python import_cookies.py
```

---

## ✅ Checklist de Uso

Toda vez que for usar:

- [ ] Abrir terminal no diretório do projeto
- [ ] Ativar ambiente virtual (`.venv\Scripts\activate`)
- [ ] Iniciar API (`uvicorn app.main:app --reload`)
- [ ] Abrir navegador em http://localhost:8001/docs
- [ ] Sincronizar cursos se necessário
- [ ] Baixar vídeos

Ou simplesmente:

- [ ] Clicar em `start_api.bat`
- [ ] Abrir http://localhost:8001/docs

---

**Pronto para começar!** 🚀

Execute `setup_rapido.bat` agora!
