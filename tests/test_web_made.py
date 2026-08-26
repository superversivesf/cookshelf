import pytest
from cooksLibrary.web.queries import get_db, toggle_made, is_made, get_made_recipes
from cooksLibrary.db import connect, migrate


@pytest.fixture
def db_conn(tmp_data_dir, monkeypatch):
    get_db.cache_clear()
    db_path = str(tmp_data_dir / "test.db")
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    conn = connect(db_path)
    migrate(conn)
    conn.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('b', 'B', '/t.pdf', 'h', 10)")
    conn.execute("INSERT INTO recipes (book_id, title, page_start) VALUES (1, 'Cake', 1), (1, 'Soup', 2)")
    conn.commit()
    return conn


def test_toggle_made_adds(db_conn):
    result = toggle_made(1)
    assert result is True
    assert is_made(1) is True

def test_toggle_made_removes(db_conn):
    toggle_made(1)
    result = toggle_made(1)
    assert result is False
    assert is_made(1) is False

def test_is_made_false_when_not_made(db_conn):
    assert is_made(1) is False

def test_get_made_recipes_ordered_by_date(db_conn):
    toggle_made(1)
    import time; time.sleep(1.0)
    toggle_made(2)
    made = get_made_recipes()
    assert len(made) == 2
    assert made[0]["title"] == "Soup"  # most recent first
    assert made[1]["title"] == "Cake"
    assert "made_at" in made[0]