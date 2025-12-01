# Análise das Requests Mapeadas - Google Classroom & Drive

**Data:** 2025-12-01
**Objetivo:** Verificar viabilidade de download de vídeos do Google Classroom

---

## 🎯 CONCLUSÃO: **SIM, É POSSÍVEL!**

Baseado na análise das requests capturadas, **é totalmente viável** fazer o download das aulas.

---

## 📊 Descobertas das Requests

### 1. **Estrutura de Vídeo do Google Drive**

Os vídeos das aulas estão hospedados no **Google Drive** e são servidos via:
- **Domínio:** `*.c.drive.google.com/videoplayback`
- **CDN:** Google Video CDN (ex: `rr5---sn-bg0e6ned.c.drive.google.com`)

### 2. **Drive Video ID Encontrado**

```
docid=1c-kpEBrrZkQs2Jp-z67C14xbuRhFxL-s
```

### 3. **URLs de Download Direto**

#### **Vídeo (video/mp4)**
```
https://rr5---sn-bg0e6ned.c.drive.google.com/videoplayback?
  expire=1764615443
  &ei=47otacuPA6aAjPgP1rmV2Qs
  &ip=185.153.176.8
  &id=4e35e057514de7ea
  &itag=134                    ← Formato: 360p video
  &source=webdrive
  &driveid=1c-kpEBrrZkQs2Jp-z67C14xbuRhFxL-s  ← ID do arquivo
  &mime=video/mp4
  &clen=137466014              ← Tamanho: ~137MB
  &dur=14718.208               ← Duração: ~4h 5min
  &sig=AJfQdSswRQ...           ← Assinatura de validação
```

#### **Áudio (audio/mp4)**
```
https://rr5---sn-bg0e6ned.c.drive.google.com/videoplayback?
  ...
  &itag=140                    ← Formato: audio AAC
  &mime=audio/mp4
  &clen=238199628              ← Tamanho: ~238MB
  &dur=14718.269
```

### 4. **Formato DASH**

O vídeo usa **DASH (Dynamic Adaptive Streaming over HTTP)**:
- Vídeo e áudio são **separados**
- Precisa baixar ambos e fazer **merge**
- Formatos:
  - `itag=134`: Video 360p (MP4)
  - `itag=140`: Audio AAC (M4A)

---

## 🔐 Autenticação & Segurança

### Cookies Necessários

As requests incluem cookies do Google:

```
SID=g.a0004AgBc...
__Secure-1PSID=g.a0004AgBc...
__Secure-3PSID=g.a0004AgBc...
HSID=AvTG7sjKweGQaFcop
SSID=AnbLQsUdYNsrZ6A0t
APISID=2iMtlmP4LVniWaRH/AUXIlZ7Cki9iwoRMb
SAPISID=y-NP5LU7Ltq_QCuU/A7XU8ut45oAj6BRWb
__Secure-1PAPISID=y-NP5LU7Ltq_QCuU/A7XU8ut45oAj6BRWb
__Secure-3PAPISID=y-NP5LU7Ltq_QCuU/A7XU8ut45oAj6BRWb
```

### Parâmetros de Segurança na URL

- `expire`: Timestamp de expiração do link (~1h)
- `sig`: Assinatura HMAC para validação
- `ip`: IP do cliente (pode ser validado)
- `requiressl=yes`: HTTPS obrigatório

---

## ✅ Estratégia de Download

### **Opção 1: yt-dlp (RECOMENDADA)**

**Por quê:**
- ✅ Suporte **nativo** para Google Drive
- ✅ Automaticamente faz merge de vídeo + áudio
- ✅ Lida com autenticação via cookies
- ✅ Retry automático em caso de falha
- ✅ Suporta range requests (download parcial)

**Como:**
```python
import yt_dlp

# URL do arquivo no Drive
drive_url = "https://drive.google.com/file/d/1c-kpEBrrZkQs2Jp-z67C14xbuRhFxL-s/view"

# Cookies extraídos da sessão autenticada
cookies = {
    'SID': 'g.a0004AgBc...',
    '__Secure-1PSID': 'g.a0004AgBc...',
    # ... outros cookies
}

# Configuração yt-dlp
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': '%(title)s.%(ext)s',
    'cookiefile': 'cookies.txt',  # Ou passar cookies via --cookies
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([drive_url])
```

### **Opção 2: Download Manual + FFmpeg**

**Passos:**
1. Extrair URLs de videoplayback (vídeo + áudio)
2. Baixar ambos os streams separadamente
3. Fazer merge com FFmpeg:
   ```bash
   ffmpeg -i video.mp4 -i audio.m4a -c copy output.mp4
   ```

**Desvantagens:**
- ❌ Mais complexo
- ❌ Precisa lidar com range requests manualmente
- ❌ Precisa gerar assinaturas válidas

---

## 🚀 Implementação no Projeto

### **1. Fluxo Completo**

```
1. OAuth2 Google → Obter cookies de sessão
2. Google Classroom API → Listar cursos e coursework
3. Extrair Drive IDs dos materiais de vídeo
4. yt-dlp com cookies → Download do vídeo
5. Armazenar localmente + metadata
```

### **2. Desafios e Soluções**

| Desafio | Solução |
|---------|---------|
| **Links expiram em ~1h** | Renovar link antes de cada download |
| **Vídeo + Áudio separados** | yt-dlp faz merge automaticamente |
| **Autenticação necessária** | Usar OAuth2 + passar cookies para yt-dlp |
| **Quotas da API** | Implementar rate limiting e caching |
| **Vídeos grandes (>1GB)** | Download com range requests + retry |

### **3. Código Exemplo**

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import yt_dlp

class ClassroomVideoDownloader:
    def __init__(self, credentials: Credentials):
        self.creds = credentials
        self.classroom = build('classroom', 'v1', credentials=credentials)
        self.drive = build('drive', 'v3', credentials=credentials)

    def get_coursework_videos(self, course_id: str) -> list[str]:
        """Extrai IDs de vídeos do Drive dos materiais do curso"""
        coursework = self.classroom.courses().courseWork().list(
            courseId=course_id
        ).execute()

        video_ids = []
        for work in coursework.get('courseWork', []):
            for material in work.get('materials', []):
                if 'driveFile' in material:
                    drive_file = material['driveFile']['driveFile']
                    if drive_file.get('mimeType', '').startswith('video/'):
                        video_ids.append(drive_file['id'])

        return video_ids

    def download_video(self, drive_file_id: str, output_path: str):
        """Baixa vídeo do Google Drive usando yt-dlp"""
        url = f"https://drive.google.com/file/d/{drive_file_id}/view"

        # Extrair cookies da sessão OAuth2
        cookies = self._extract_cookies_from_credentials()

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{output_path}/%(id)s.%(ext)s',
            'cookiefile': 'cookies.txt',  # Salvar cookies em arquivo
            'merge_output_format': 'mp4',
            'progress_hooks': [self._progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    def _progress_hook(self, d):
        """Callback para tracking de progresso"""
        if d['status'] == 'downloading':
            print(f"Progress: {d['_percent_str']}")
        elif d['status'] == 'finished':
            print(f"Download complete: {d['filename']}")
```

---

## ⚠️ Limitações e Considerações

### 1. **Quotas da Google Classroom API**

- **10,000 requests/day** (padrão)
- **20 queries/second/user**
- Implementar caching para reduzir chamadas

### 2. **Tamanho dos Vídeos**

- Vídeos de aula podem ter **1-2 GB** cada
- Implementar:
  - Progress tracking
  - Resume on failure
  - Cleanup de arquivos parciais

### 3. **Expiração de Tokens**

- OAuth2 tokens expiram (~1h)
- Links de videoplayback expiram (~1h)
- Implementar refresh automático

### 4. **Compliance**

- ⚠️ Respeitar termos de uso do Google Classroom
- ⚠️ Apenas baixar conteúdo autorizado
- ⚠️ Uso educacional/pessoal

---

## 📦 Dependências Necessárias

```txt
# Core
google-auth==2.37.0
google-auth-oauthlib==1.2.1
google-api-python-client==2.159.0

# Download
yt-dlp==2024.12.23

# FFmpeg (system dependency)
# apt-get install ffmpeg  # Linux
# brew install ffmpeg     # Mac
```

---

## 🎯 Próximos Passos

1. ✅ **Análise de viabilidade** - COMPLETO
2. ⏳ **Setup do projeto** - Criar estrutura de diretórios
3. ⏳ **Implementar OAuth2** - Autenticação Google
4. ⏳ **Classroom API integration** - Listar cursos e materiais
5. ⏳ **Video downloader** - Implementar com yt-dlp
6. ⏳ **Workers assíncronos** - Fila de downloads
7. ⏳ **API REST** - Endpoints para gerenciar downloads

---

## 🔍 Observações Técnicas

### **ITAGs do Google (formato)**

```
Video:
- 134: 360p (MP4, H.264)
- 135: 480p
- 136: 720p
- 137: 1080p

Audio:
- 140: AAC 128kbps (M4A)
- 141: AAC 256kbps
```

### **Exemplo de Request Completa**

```bash
curl 'https://rr5---sn-bg0e6ned.c.drive.google.com/videoplayback?...' \
  -H 'Cookie: SID=...; APISID=...' \
  -H 'User-Agent: Mozilla/5.0 ...' \
  --output video.mp4
```

---

**CONCLUSÃO FINAL:** ✅ **É TOTALMENTE POSSÍVEL fazer o download das aulas usando yt-dlp + Google APIs + OAuth2.**
