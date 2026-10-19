"""Gera a pasta e o zip "Para colaboradores" a partir de public/.

O pacote é um único HTML com CSS e JS embutidos. Ele abre com dois cliques
no Windows e no Mac, sem Python, servidor local ou permissão de execução.

Uso: python scripts/build_colaboradores.py
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
OUT_DIR = ROOT / "Para colaboradores"
OUT_ZIP = ROOT / "Para colaboradores.zip"
HTML_NAME = "Abrir transcricao.html"

LEIA_ME = """\
Como usar

1. Se recebeu um .zip, extraia antes (botão direito > Extrair tudo, no Windows;
   dois cliques no zip, no Mac).
2. Dê dois cliques em "Abrir transcricao.html".
3. O navegador abre. Arraste o áudio.

Na primeira vez o navegador baixa o modelo (cerca de 80 MB), então precisa de internet.
O áudio não sai do computador.

Use Chrome, Edge ou Firefox atualizados.
Se o arquivo abrir em outro programa, clique com o botão direito >
Abrir com > Chrome (ou Edge).
"""


def _replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"Esperava exatamente um trecho {old!r} para embutir.")
    return text.replace(old, new)


def build_html() -> str:
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    css = (PUBLIC / "static" / "app.css").read_text(encoding="utf-8")
    fmt = (PUBLIC / "static" / "format.js").read_text(encoding="utf-8")
    app = (PUBLIC / "static" / "app.js").read_text(encoding="utf-8")

    # Imports relativos não funcionam em file://; junta os dois módulos num só.
    fmt = re.sub(r"^export\s+", "", fmt, flags=re.MULTILINE)
    app = _replace_once(app, 'import { buildTranscript } from "./format.js";\n', "")
    script = fmt + "\n" + app

    for chunk in (css, script):
        if "</style" in chunk or "</script" in chunk:
            raise SystemExit("O conteúdo embutido não pode conter </style ou </script.")

    html = _replace_once(
        html,
        '<link rel="stylesheet" href="/static/app.css" />',
        "<style>\n" + css + "\n</style>",
    )
    html = _replace_once(
        html,
        '<script type="module" src="/static/app.js"></script>',
        '<script type="module">\n' + script + "\n</script>",
    )
    return html


def write_zip(files: dict[str, bytes]) -> None:
    tmp = OUT_ZIP.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            # Caminhos com "/" e criados como Unix: o Mac extrai sem nomes quebrados.
            info = zipfile.ZipInfo("Para colaboradores/" + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)
    tmp.replace(OUT_ZIP)


def main() -> None:
    files = {
        HTML_NAME: build_html().encode("utf-8"),
        # BOM para o Bloco de Notas antigo mostrar os acentos.
        "Leia-me.txt": ("﻿" + LEIA_ME).replace("\n", "\r\n").encode("utf-8"),
    }

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()
    for name, data in files.items():
        (OUT_DIR / name).write_bytes(data)
    write_zip(files)
    print(f"Gerado: {OUT_DIR}")
    print(f"Gerado: {OUT_ZIP}")


if __name__ == "__main__":
    main()
