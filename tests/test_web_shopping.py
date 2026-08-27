import pytest
from fastapi.testclient import TestClient
from cooksLibrary.web.main import create_app
from cooksLibrary.web.queries import get_db, _clear_db_cache, add_recipe_to_shopping_list, get_shopping_list, toggle_shopping_list_item, clear_shopping_list
from cooksLibrary.db import connect, migrate


@pytest.fixture
def client(tmp_data_dir, monkeypatch):
    _clear_db_cache()
    db_path = str(tmp_data_dir / "test.db")
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    conn = connect(db_path)
    migrate(conn)
    conn.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('b', 'B', '/t.pdf', 'h', 10)")
    conn.execute("INSERT INTO recipes (book_id, title, page_start, servings, confidence, render_method) VALUES (1, 'Test Cake', 1, '8', 0.9, 'structured')")
    conn.execute("INSERT INTO recipe_ingredients (recipe_id, position, section, quantity, unit, ingredient_name, note, raw_text) VALUES (1, 0, '', '2', 'cups', 'flour', '', '2 cups flour')")
    conn.execute("INSERT INTO recipe_ingredients (recipe_id, position, section, quantity, unit, ingredient_name, note, raw_text) VALUES (1, 1, '', '1', 'tsp', 'salt', '', '1 tsp salt')")
    conn.commit()
    conn.close()
    return TestClient(create_app())


def test_shopping_page_empty(client):
    r = client.get("/shopping")
    assert r.status_code == 200
    assert "empty" in r.text.lower()

def test_add_recipe_to_shopping_list(client):
    r = client.post("/shopping/add/1", follow_redirects=False)
    assert r.status_code == 303
    r = client.get("/shopping")
    assert r.status_code == 200
    assert "2 cups flour" in r.text
    assert "1 tsp salt" in r.text
    assert "Test Cake" in r.text

def test_toggle_shopping_item(client):
    client.post("/shopping/add/1")
    items = get_shopping_list()
    item_id = items[0]["id"]
    result = toggle_shopping_list_item(item_id)
    assert result is True
    items = get_shopping_list()
    assert items[0]["checked"] == 1
    result = toggle_shopping_list_item(item_id)
    assert result is False
    items = get_shopping_list()
    assert items[0]["checked"] == 0

def test_clear_shopping_list(client):
    client.post("/shopping/add/1")
    assert len(get_shopping_list()) == 2
    clear_shopping_list()
    assert len(get_shopping_list()) == 0

def test_add_replaces_existing_list(client):
    conn = connect(str(client.app.dependency_overrides.get("db", {}).get("path", ""))) if False else None
    client.post("/shopping/add/1")
    assert len(get_shopping_list()) == 2
    # Add again — should replace, not append
    client.post("/shopping/add/1")
    assert len(get_shopping_list()) == 2