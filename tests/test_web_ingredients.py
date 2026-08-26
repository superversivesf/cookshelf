import pytest
from fastapi.testclient import TestClient
from cooksLibrary.web.main import create_app
from cooksLibrary.web.queries import get_db, _clear_db_cache
from cooksLibrary.db import connect, migrate
from cooksLibrary.ingest.index import rebuild_ingredient_index

@pytest.fixture
def client(tmp_data_dir, monkeypatch):
    _clear_db_cache()
    db_path = str(tmp_data_dir / "test.db")
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    conn = connect(db_path)
    migrate(conn)
    conn.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('b', 'B', '/t.pdf', 'h', 10)")
    conn.execute("INSERT INTO recipes (book_id, title, page_start) VALUES (1, 'Cake', 1)")
    conn.execute("INSERT INTO recipe_ingredients (recipe_id, position, ingredient_name, raw_text) VALUES (1, 0, 'flour', '2 cups flour')")
    conn.commit()
    rebuild_ingredient_index(conn)
    conn.close()
    return TestClient(create_app())

def test_ingredient_list(client):
    r = client.get("/ingredients")
    assert r.status_code == 200
    assert "Flour" in r.text
    assert "list-group" in r.text.lower()

def test_ingredient_detail(client):
    r = client.get("/ingredients/flour")
    assert r.status_code == 200
    assert "Cake" in r.text