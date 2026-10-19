import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from transcriber import transcribe_file

app = FastAPI(title="Transcrição")
STATIC_DIR = Path(__file__).parent / "public"


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/transcribe")
async def transcribe(video: UploadFile = File(...)):
    if not video.filename:
        raise HTTPException(400, "Nenhum arquivo enviado.")

    suffix = Path(video.filename).suffix.lower()
    if not suffix:
        raise HTTPException(400, "Arquivo sem extensão.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(video.file, tmp)
            tmp_path = Path(tmp.name)

        result = transcribe_file(tmp_path, original_name=Path(video.filename).name)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(500, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Erro na transcrição: {e}") from e
    finally:
        if "tmp_path" in locals() and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")
