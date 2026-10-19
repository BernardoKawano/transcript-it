import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

_model = None

LANGUAGE_NAMES = {
    "pt": "português",
    "en": "inglês",
    "es": "espanhol",
    "fr": "francês",
    "de": "alemão",
    "it": "italiano",
    "ja": "japonês",
    "ko": "coreano",
    "zh": "chinês",
    "ru": "russo",
    "ar": "árabe",
    "nl": "holandês",
    "pl": "polonês",
    "sv": "sueco",
    "tr": "turco",
    "hi": "hindi",
    "uk": "ucraniano",
}


def get_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper não está instalado. Rode o instalador do seu sistema "
                "(run.bat no Windows ou bash run.sh no Mac)."
            ) from exc
        size = os.getenv("WHISPER_MODEL", "base")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute = os.getenv("WHISPER_COMPUTE", "int8")
        _model = WhisperModel(size, device=device, compute_type=compute)
    return _model


def _resolve_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    raise RuntimeError(
        "ffmpeg não encontrado. Instale o FFmpeg no PATH ou use imageio-ffmpeg."
    )


def extract_audio(video_path: Path, audio_path: Path) -> None:
    cmd = [
        _resolve_ffmpeg(),
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


def format_clock(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_duration_label(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    parts: list[str] = []
    if h:
        parts.append(f"{h} h")
    if m:
        parts.append(f"{m} min")
    if s or not parts:
        parts.append(f"{s} s")
    return " ".join(parts)


def language_label(code: str | None) -> str:
    if not code:
        return "idioma não identificado"
    return LANGUAGE_NAMES.get(code, code)


def count_label(n: int) -> str:
    if n == 1:
        return "1 trecho"
    return f"{n} trechos"


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _as_rows(segments) -> list[tuple[float, float, str]]:
    rows: list[tuple[float, float, str]] = []
    for seg in segments:
        if isinstance(seg, tuple):
            start, end, text = seg
        else:
            start, end, text = seg.start, seg.end, seg.text
        text = str(text).strip()
        if not text:
            continue
        rows.append((float(start), float(end), text))
    return rows


def build_pure(segments) -> str:
    return "\n".join(text for _, _, text in _as_rows(segments))


def build_timestamped(segments) -> str:
    lines: list[str] = []
    for start, end, text in _as_rows(segments):
        duration = end - start
        lines.append(
            f"[{format_time(start)} --> {format_time(end)}] "
            f"({duration:.2f}s) {text}"
        )
    return "\n".join(lines)


def build_readable(
    segments,
    *,
    filename: str,
    language: str | None,
    duration: float | None,
) -> str:
    rows = _as_rows(segments)
    total = duration if duration is not None else (rows[-1][1] if rows else 0.0)
    lines = [
        filename,
        f"{format_duration_label(total)} · {language_label(language)} · {count_label(len(rows))}",
        "",
    ]
    if not rows:
        lines.extend(["Nenhuma fala detectada.", ""])
        return "\n".join(lines)
    for start, _, text in rows:
        lines.append(format_clock(start))
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def build_ai_file(
    segments,
    *,
    filename: str,
    language: str | None,
    duration: float | None,
    generated_at: datetime | None = None,
) -> str:
    rows = _as_rows(segments)
    total = duration if duration is not None else (rows[-1][1] if rows else 0.0)
    when = generated_at or datetime.now().astimezone()
    stamp = when.isoformat(timespec="seconds")
    lines = [
        "---",
        "tipo: transcricao",
        f"origem: {yaml_quote(filename)}",
        f"idioma: {language or 'desconhecido'}",
        f"duracao_segundos: {total:.3f}",
        f"segmentos: {len(rows)}",
        f"gerado_em: {stamp}",
        "---",
        "",
        "# Transcrição para IA",
        "",
        "Este arquivo é a transcrição integral de um áudio.",
        "Use apenas o que está escrito abaixo.",
        "Se uma informação não aparecer na transcrição, diga que ela não consta.",
        "Não invente falas, nomes, decisões ou números.",
        "",
        "## Contexto",
        "",
        f"- Arquivo: {filename}",
        f"- Duração: {format_duration_label(total)}",
        f"- Idioma: {language_label(language)}",
        f"- Trechos: {len(rows)}",
        "",
        "## Texto",
        "",
    ]
    if rows:
        lines.extend(text for _, _, text in rows)
    else:
        lines.append("Nenhuma fala detectada.")
    lines.extend(["", "## Linha do tempo", ""])
    if rows:
        for start, end, text in rows:
            lines.append(
                f"- [{format_time(start)}–{format_time(end)}] ({end - start:.2f}s) {text}"
            )
    else:
        lines.append("- Nenhuma fala detectada.")
    lines.append("")
    return "\n".join(lines)


def build_segments(segments) -> list[dict]:
    payload: list[dict] = []
    for start, end, text in _as_rows(segments):
        payload.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "label": format_clock(start),
                "text": text,
            }
        )
    return payload


def build_transcript(
    segments,
    *,
    filename: str,
    language: str | None,
    duration: float | None,
    generated_at: datetime | None = None,
) -> dict:
    rows = _as_rows(segments)
    total = duration if duration is not None else (rows[-1][1] if rows else 0.0)
    return {
        "pure": build_pure(rows),
        "timestamped": build_timestamped(rows),
        "readable": build_readable(
            rows, filename=filename, language=language, duration=total
        ),
        "ai_file": build_ai_file(
            rows,
            filename=filename,
            language=language,
            duration=total,
            generated_at=generated_at,
        ),
        "segments": build_segments(rows),
        "meta": {
            "filename": filename,
            "language": language,
            "language_label": language_label(language),
            "duration": round(total, 3),
            "duration_label": format_duration_label(total),
            "segment_count": len(rows),
        },
    }


def transcribe_file(file_path: Path, original_name: str | None = None) -> dict:
    suffix = file_path.suffix.lower()
    video_ext = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".wmv", ".flv"}
    audio_ext = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}

    if suffix not in video_ext | audio_ext:
        raise ValueError(f"Formato não suportado: {suffix}")

    filename = Path(original_name).name if original_name else file_path.name

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        audio_path = tmp_dir / "audio.wav"

        if suffix in video_ext:
            extract_audio(file_path, audio_path)
            source = audio_path
        else:
            source = file_path

        model = get_model()
        segments, info = model.transcribe(
            str(source),
            beam_size=5,
            vad_filter=True,
        )
        rows = _as_rows(segments)
        language = getattr(info, "language", None)
        duration = getattr(info, "duration", None)

    return build_transcript(
        rows,
        filename=filename,
        language=language,
        duration=duration,
    )
