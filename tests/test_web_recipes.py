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
    conn.execute(
        "INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('b', 'B', '/t.pdf', 'h', 10)"
    )
    conn.execute("""INSERT INTO recipes (book_id, title, page_start, description, servings,
                    instructions, confidence, render_method)
                    VALUES (1, 'Test Cake', 1, 'A test cake.', '8', 'Mix and bake.', 0.9, 'structured')""")
    conn.execute("""INSERT INTO recipe_ingredients (recipe_id, position, section, quantity,
                    unit, ingredient_name, note, raw_text)
                    VALUES (1, 0, '', '2', 'cups', 'flour', '', '2 cups flour')""")
    conn.commit()
    conn.close()
    return TestClient(create_app())


def test_recipe_view_structured(client):
    r = client.get("/recipes/1")
    assert r.status_code == 200
    assert "Test Cake" in r.text
    assert "flour" in r.text
    assert "Mix and bake." in r.text


def test_recipe_view_404(client):
    r = client.get("/recipes/999")
    assert r.status_code == 404
