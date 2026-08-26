import pytest
from fastapi.testclient import TestClient
from cooksLibrary.web.main import create_app
from cooksLibrary.web.queries import get_db, _clear_db_cache
from cooksLibrary.db import connect, migrate

@pytest.fixture
def client(tmp_data_dir, monkeypatch):
    _clear_db_cache()
    monkeypatch.setenv("COOKS_DB_PATH", str(tmp_data_dir / "test.db"))
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    app = create_app()
    return TestClient(app)

@pytest.fixture
def populated_client(tmp_data_dir, monkeypatch):
    _clear_db_cache()
    db_path = str(tmp_data_dir / "test.db")
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    conn = connect(db_path)
    migrate(conn)
    conn.execute("INSERT INTO books (slug, title, category, source_path, source_hash, page_count) VALUES ('test-book', 'Test Book', 'Desserts & Baking', '/t.pdf', 'h1', 10)")
    conn.execute("INSERT INTO recipes (book_id, title, page_start, servings, confidence) VALUES (1, 'Cake', 1, '8', 0.9)")
    conn.commit()
    conn.close()
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
    assert "bootstrap" in r.text.lower()
    assert "navbar" in r.text.lower()

def test_book_list(populated_client):
    r = populated_client.get("/books")
    assert r.status_code == 200
    assert "Test Book" in r.text
    assert "Desserts &amp; Baking" in r.text
    assert "card" in r.text.lower()

def test_book_detail(populated_client):
    r = populated_client.get("/books/test-book")
    assert r.status_code == 200
    assert "Test Book" in r.text
    assert "Cake" in r.text