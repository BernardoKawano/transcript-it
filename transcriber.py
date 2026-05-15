import os
import subprocess
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        size = os.getenv("WHISPER_MODEL", "base")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute = os.getenv("WHISPER_COMPUTE", "int8")
        _model = WhisperModel(size, device=device, compute_type=compute)
    return _model


def extract_audio(video_path: Path, audio_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg falhou. Instale o FFmpeg e adicione ao PATH.\n"
            + (result.stderr or result.stdout or "")
        )


def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:06.3f}"
    return f"{m:02d}:{s:06.3f}"


def transcribe_file(file_path: Path) -> dict[str, str]:
    suffix = file_path.suffix.lower()
    video_ext = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".wmv", ".flv"}
    audio_ext = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}

    if suffix not in video_ext | audio_ext:
        raise ValueError(f"Formato não suportado: {suffix}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        audio_path = tmp_dir / "audio.wav"

        if suffix in video_ext:
            extract_audio(file_path, audio_path)
            source = audio_path
        else:
            source = file_path

        model = get_model()
        segments, _info = model.transcribe(
            str(source),
            beam_size=5,
            vad_filter=True,
        )

        pure_lines: list[str] = []
        timed_lines: list[str] = []

        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            pure_lines.append(text)
            start = seg.start
            end = seg.end
            duration = end - start
            timed_lines.append(
                f"[{format_time(start)} --> {format_time(end)}] "
                f"({duration:.2f}s) {text}"
            )

    return {
        "pure": "\n".join(pure_lines),
        "timestamped": "\n".join(timed_lines),
    }
