import pytest
from fastapi.testclient import TestClient
from cooksLibrary.web.main import create_app
from cooksLibrary.web.queries import get_db
from cooksLibrary.db import connect, migrate


@pytest.fixture
def client(tmp_data_dir, monkeypatch):
    get_db.cache_clear()
    db_path = str(tmp_data_dir / "test.db")
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    conn = connect(db_path)
    migrate(conn)
    conn.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('b', 'B', '/t.pdf', 'h', 10)")
    conn.execute("INSERT INTO recipes (book_id, title, page_start) VALUES (1, 'Cake', 1)")
    conn.commit()
    conn.close()
    return TestClient(create_app())


def test_toggle_bookmark(client):
    r = client.post("/bookmarks", data={"recipe_id": "1"})
    assert r.status_code == 200
    assert "bg-red-500" in r.text
    assert "Bookmarked" in r.text
    r = client.post("/bookmarks", data={"recipe_id": "1"})
    assert r.status_code == 200
    assert "bg-stone-200" in r.text
    assert "Bookmarked" not in r.text


def test_delete_bookmark(client):
    client.post("/bookmarks", data={"recipe_id": "1"})
    r = client.delete("/bookmarks/1")
    assert r.status_code == 204
    bookmarks = client.get("/bookmarks")
    assert "Cake" not in bookmarks.text


def test_bookmarks_page(client):
    client.post("/bookmarks", data={"recipe_id": "1"})
    r = client.get("/bookmarks")
    assert r.status_code == 200
    assert "Cake" in r.text