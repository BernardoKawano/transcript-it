import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


def test_home_and_static_assets_load():
    client = TestClient(main.app)
    home = client.get("/")
    assert home.status_code == 200
    assert "Arquivo para IA" in home.text
    assert 'src="/static/app.js"' in home.text

    script = client.get("/static/app.js")
    style = client.get("/static/app.css")
    assert script.status_code == 200
    assert "transcribe" in script.text
    assert style.status_code == 200
    assert ".segment" in style.text


def test_text_upload_is_rejected_before_model(monkeypatch):
    def boom():
        raise AssertionError("modelo não deveria carregar")

    monkeypatch.setattr("transcriber.get_model", boom)
    client = TestClient(main.app)
    response = client.post(
        "/api/transcribe",
        files={"video": ("pauta.txt", b"pauta da reuniao", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Formato não suportado: .txt"
