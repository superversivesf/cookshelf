import pytest
from fastapi.testclient import TestClient
from cooksLibrary.web.main import create_app
from cooksLibrary.web.queries import get_db
from cooksLibrary.db import connect, migrate
from cooksLibrary.ingest.index import rebuild_fts

@pytest.fixture
def client(tmp_data_dir, monkeypatch):
    get_db.cache_clear()
    db_path = str(tmp_data_dir / "test.db")
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    conn = connect(db_path)
    migrate(conn)
    conn.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('b', 'B', '/t.pdf', 'h', 10)")
    conn.execute("INSERT INTO recipes (book_id, title, page_start, description, instructions) VALUES (1, 'Chocolate Cake', 1, 'Rich dessert', 'Bake at 350')")
    conn.commit()
    rebuild_fts(conn)
    conn.close()
    return TestClient(create_app())

def test_search_returns_results(client):
    r = client.get("/search", params={"q": "chocolate"})
    assert r.status_code == 200
    assert "Chocolate Cake" in r.text

def test_search_empty_query(client):
    r = client.get("/search", params={"q": ""})
    assert r.status_code == 200

def test_search_special_characters(client):
    r = client.get("/search", params={"q": "chocolate (cake"})
    assert r.status_code == 200