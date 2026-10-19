#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

LOG="$(pwd)/ultimo_erro.log"
echo "[$(date)] Iniciando..." > "$LOG"

if [[ ! -x .venv/bin/python ]]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: Python 3 nao encontrado." | tee -a "$LOG"
    echo "Instale em https://www.python.org/downloads/ e rode este script de novo."
    exit 1
  fi
  echo "Criando ambiente virtual (primeira vez)..."
  python3 -m venv .venv
  echo "Instalando dependencias..."
  .venv/bin/python -m pip install -r requirements.txt >> "$LOG" 2>&1
fi

if ! .venv/bin/python -c "import faster_whisper" >/dev/null 2>&1; then
  echo "Instalando dependencias que faltam..."
  .venv/bin/python -m pip install -r requirements.txt >> "$LOG" 2>&1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "AVISO: FFmpeg nao esta no PATH. Videos usam o ffmpeg embutido, se a instalacao tiver imageio-ffmpeg." | tee -a "$LOG"
fi

URL="http://127.0.0.1:8000"
echo
echo "========================================"
echo "  Transcricao"
echo "  $URL"
echo "========================================"
echo

if command -v open >/dev/null 2>&1; then
  open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi

exec .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
