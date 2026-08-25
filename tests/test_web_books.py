import pytest
from fastapi.testclient import TestClient
from cooksLibrary.web.main import create_app

@pytest.fixture
def client(tmp_data_dir, monkeypatch):
    monkeypatch.setenv("COOKS_DB_PATH", str(tmp_data_dir / "test.db"))
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    app = create_app()
    return TestClient(app)

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_home_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "<html" in r.text.lower()