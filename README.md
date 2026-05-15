# transcript-it

Ferramenta web para transcrever vídeos e áudios em texto, com versão pura e com timestamps por frase.

## Requisitos

- Python 3.11+
- [FFmpeg](https://ffmpeg.org/) no PATH (necessário para arquivos de vídeo)

## Uso rápido (Windows)

1. Execute `run.bat` (ou dê duplo clique em `Iniciar.vbs`)
2. O navegador abrirá em http://127.0.0.1:8000
3. Envie um arquivo e clique em **Transcrever**

## Instalação manual

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Testes

```bash
.venv\Scripts\activate
pytest
```

## Deploy no Vercel

O repositório está configurado para deploy automático via GitHub:

1. Conecte o repo [transcript-it](https://github.com/BernardoKawano/transcript-it) no [Vercel Dashboard](https://vercel.com/new)
2. Cada push na branch `main` gera um novo deploy
3. URL de produção: https://transcript-it.vercel.app

Variáveis de ambiente opcionais no Vercel:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `WHISPER_MODEL` | `base` | Tamanho do modelo (`tiny`, `base`, `small`) |
| `WHISPER_DEVICE` | `cpu` | Dispositivo de inferência |
| `WHISPER_COMPUTE` | `int8` | Tipo de computação |

## Estrutura

- `main.py` — API FastAPI
- `transcriber.py` — lógica de transcrição (faster-whisper)
- `public/` — interface web (servida pelo CDN no Vercel)
