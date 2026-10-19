import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transcriber import (
    build_ai_file,
    build_readable,
    build_timestamped,
    build_transcript,
    format_clock,
    format_duration_label,
    format_time,
    language_label,
    transcribe_file,
)

# Trecho real de uma reunião curta, no formato que o Whisper devolve.
REUNIAO = [
    (0.0, 4.2, "Bom dia, pessoal. Vamos revisar o áudio da reunião."),
    (4.2, 9.8, "O combinado é enviar a transcrição para o time ainda hoje."),
    (72.5, 80.0, "Ficou definido que o arquivo para IA sai em Markdown."),
]

GERADO_EM = datetime(2026, 9, 23, 13, 22, tzinfo=timezone(timedelta(hours=-3)))


def test_format_time_under_one_hour():
    assert format_time(0) == "00:00.000"
    assert format_time(65.5) == "01:05.500"


def test_format_time_with_hours():
    assert format_time(3661.25) == "01:01:01.250"


def test_format_clock_drops_milliseconds():
    assert format_clock(0) == "00:00"
    assert format_clock(65.9) == "01:05"
    assert format_clock(3661.25) == "01:01:01"


def test_format_duration_label_from_meeting_length():
    assert format_duration_label(45) == "45 s"
    assert format_duration_label(80) == "1 min 20 s"
    assert format_duration_label(3661) == "1 h 1 min 1 s"


def test_language_label_portuguese():
    assert language_label("pt") == "português"
    assert language_label(None) == "idioma não identificado"


def test_readable_view_uses_clock_and_plain_sentences():
    text = build_readable(
        REUNIAO,
        filename="reuniao-produto.mp3",
        language="pt",
        duration=80.0,
    )
    assert text == (
        "reuniao-produto.mp3\n"
        "1 min 20 s · português · 3 trechos\n"
        "\n"
        "00:00\n"
        "Bom dia, pessoal. Vamos revisar o áudio da reunião.\n"
        "\n"
        "00:04\n"
        "O combinado é enviar a transcrição para o time ainda hoje.\n"
        "\n"
        "01:12\n"
        "Ficou definido que o arquivo para IA sai em Markdown.\n"
    )


def test_ai_file_is_markdown_with_instructions_and_timeline():
    text = build_ai_file(
        REUNIAO,
        filename='reuniao "produto".mp3',
        language="pt",
        duration=80.0,
        generated_at=GERADO_EM,
    )
    assert text == (
        "---\n"
        "tipo: transcricao\n"
        'origem: "reuniao \\"produto\\".mp3"\n'
        "idioma: pt\n"
        "duracao_segundos: 80.000\n"
        "segmentos: 3\n"
        "gerado_em: 2026-09-23T13:22:00-03:00\n"
        "---\n"
        "\n"
        "# Transcrição para IA\n"
        "\n"
        "Este arquivo é a transcrição integral de um áudio.\n"
        "Use apenas o que está escrito abaixo.\n"
        "Se uma informação não aparecer na transcrição, diga que ela não consta.\n"
        "Não invente falas, nomes, decisões ou números.\n"
        "\n"
        "## Contexto\n"
        "\n"
        '- Arquivo: reuniao "produto".mp3\n'
        "- Duração: 1 min 20 s\n"
        "- Idioma: português\n"
        "- Trechos: 3\n"
        "\n"
        "## Texto\n"
        "\n"
        "Bom dia, pessoal. Vamos revisar o áudio da reunião.\n"
        "O combinado é enviar a transcrição para o time ainda hoje.\n"
        "Ficou definido que o arquivo para IA sai em Markdown.\n"
        "\n"
        "## Linha do tempo\n"
        "\n"
        "- [00:00.000–00:04.200] (4.20s) Bom dia, pessoal. Vamos revisar o áudio da reunião.\n"
        "- [00:04.200–00:09.800] (5.60s) O combinado é enviar a transcrição para o time ainda hoje.\n"
        "- [01:12.500–01:20.000] (7.50s) Ficou definido que o arquivo para IA sai em Markdown.\n"
    )


def test_timestamped_keeps_previous_line_format():
    text = build_timestamped([(0.0, 4.2, "Bom dia, pessoal.")])
    assert text == "[00:00.000 --> 00:04.200] (4.20s) Bom dia, pessoal."


def test_transcript_payload_has_visual_segments_and_ai_file():
    payload = build_transcript(
        REUNIAO,
        filename="reuniao-produto.mp3",
        language="pt",
        duration=80.0,
        generated_at=GERADO_EM,
    )
    assert payload["segments"][2]["label"] == "01:12"
    assert payload["segments"][2]["text"].startswith("Ficou definido")
    assert payload["meta"]["segment_count"] == 3
    assert payload["meta"]["language_label"] == "português"
    assert "Arquivo para IA" in payload["ai_file"] or "# Transcrição para IA" in payload["ai_file"]
    assert payload["readable"].startswith("reuniao-produto.mp3\n")


def test_empty_audio_still_returns_both_formats():
    payload = build_transcript(
        [],
        filename="silencio.wav",
        language=None,
        duration=3.0,
        generated_at=GERADO_EM,
    )
    assert "Nenhuma fala detectada." in payload["readable"]
    assert "Nenhuma fala detectada." in payload["ai_file"]
    assert payload["segments"] == []
    assert payload["meta"]["segment_count"] == 0


def test_unsupported_format_does_not_load_model(tmp_path, monkeypatch):
    def boom():
        raise AssertionError("modelo não deveria carregar")

    monkeypatch.setattr("transcriber.get_model", boom)
    notes = tmp_path / "pauta.txt"
    notes.write_text("só uma pauta, não é áudio", encoding="utf-8")

    with pytest.raises(ValueError, match="Formato não suportado"):
        transcribe_file(notes, original_name="pauta.txt")
