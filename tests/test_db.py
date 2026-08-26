from cooksLibrary.db import connect, migrate

def test_migrate_creates_all_tables(tmp_db):
    migrate(tmp_db)
    tables = {row["name"] for row in tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    expected = {"books", "recipes", "recipe_ingredients", "ingredient_index",
                "bookmarks", "recipes_fts"}
    assert expected.issubset(tables)

def test_migrate_is_idempotent(tmp_db):
    migrate(tmp_db)
    migrate(tmp_db)  # should not raise
    tables = {row["name"] for row in tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "books" in tables

def test_migrate_creates_made_recipes_table(tmp_db):
    migrate(tmp_db)
    tables = {row["name"] for row in tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "made_recipes" in tables