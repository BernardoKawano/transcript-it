import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_colaboradores as build


def test_html_is_self_contained():
    html = build.build_html()
    assert "/static/" not in html
    assert "./format.js" not in html
    assert "\nexport " not in html
    assert "function buildTranscript" in html
    assert 'id="languageSelect"' in html
    assert ".segment" in html


def test_zip_opens_on_mac(tmp_path, monkeypatch):
    out_zip = tmp_path / "pacote.zip"
    monkeypatch.setattr(build, "OUT_ZIP", out_zip)
    build.write_zip({build.HTML_NAME: b"<html></html>", "Leia-me.txt": b"oi"})

    with zipfile.ZipFile(out_zip) as zf:
        infos = zf.infolist()
    names = [info.filename for info in infos]
    assert names == [
        "Para colaboradores/Abrir transcricao.html",
        "Para colaboradores/Leia-me.txt",
    ]
    for info in infos:
        assert "\\" not in info.filename
        assert info.create_system == 3
