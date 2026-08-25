from cooksLibrary.db import migrate
from cooksLibrary.ingest.index import rebuild_fts, rebuild_ingredient_index

def test_rebuild_fts_populates(tmp_db):
    migrate(tmp_db)
    tmp_db.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('t', 'T', '/t.pdf', 'h1', 10)")
    tmp_db.execute("INSERT INTO recipes (book_id, title, page_start, description, instructions) VALUES (1, 'Cake', 1, 'A cake', 'Bake it')")
    tmp_db.execute("INSERT INTO recipe_ingredients (recipe_id, position, ingredient_name, raw_text) VALUES (1, 0, 'flour', '2 cups flour')")
    tmp_db.commit()
    rebuild_fts(tmp_db)
    row = tmp_db.execute("SELECT title FROM recipes_fts WHERE recipes_fts MATCH 'cake'").fetchone()
    assert row is not None
    assert row["title"] == "Cake"

def test_rebuild_ingredient_index_counts(tmp_db):
    migrate(tmp_db)
    tmp_db.execute("INSERT INTO books (slug, title, source_path, source_hash, page_count) VALUES ('t', 'T', '/t.pdf', 'h1', 10)")
    tmp_db.execute("INSERT INTO recipes (book_id, title, page_start) VALUES (1, 'A', 1), (2, 'B', 2)")
    # Need separate book for second recipe — fix: use same book, two recipes
    tmp_db.execute("INSERT INTO recipe_ingredients (recipe_id, position, ingredient_name, raw_text) VALUES (1, 0, 'flour', 'x'), (1, 1, 'sugar', 'y'), (2, 0, 'flour', 'z')")
    tmp_db.commit()
    rebuild_ingredient_index(tmp_db)
    flour = tmp_db.execute("SELECT * FROM ingredient_index WHERE ingredient_name = 'flour'").fetchone()
    assert flour["recipe_count"] == 2
    sugar = tmp_db.execute("SELECT * FROM ingredient_index WHERE ingredient_name = 'sugar'").fetchone()
    assert sugar["recipe_count"] == 1