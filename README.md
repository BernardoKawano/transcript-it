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

## Estrutura

- `main.py` — API FastAPI
- `transcriber.py` — lógica de transcrição (faster-whisper)
- `static/` — interface web
