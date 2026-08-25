import sqlite3
from functools import lru_cache
from ..config import get_settings
from ..db import connect, migrate

@lru_cache(maxsize=1)
def get_db() -> sqlite3.Connection:
    settings = get_settings()
    conn = connect(settings.db_path)
    migrate(conn)
    return conn

def get_books_by_category() -> list[dict]:
    conn = get_db()
    return [dict(r) for r in conn.execute(
        "SELECT * FROM books ORDER BY category, title"
    ).fetchall()]

def get_book_by_slug(slug: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM books WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else None

def get_recipes_for_book(book_id: int) -> list[dict]:
    conn = get_db()
    return [dict(r) for r in conn.execute(
        "SELECT * FROM recipes WHERE book_id = ? ORDER BY page_start", (book_id,)
    ).fetchall()]

def get_recipe(recipe_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if not row:
        return None
    recipe = dict(row)
    recipe["ingredients"] = [dict(r) for r in conn.execute(
        "SELECT * FROM recipe_ingredients WHERE recipe_id = ? ORDER BY position",
        (recipe_id,)
    ).fetchall()]
    return recipe

def search_recipes(query: str, limit: int = 20, offset: int = 0) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id, r.title, r.page_start, b.slug AS book_slug, b.title AS book_title,
               snippet(recipes_fts, 1, '<mark>', '</mark>', '...', 20) AS snippet
        FROM recipes_fts fts
        JOIN recipes r ON r.id = fts.rowid
        JOIN books b ON b.id = r.book_id
        WHERE recipes_fts MATCH ?
        LIMIT ? OFFSET ?
    """, (query, limit, offset)).fetchall()
    return [dict(r) for r in rows]

def get_bookmarks() -> list[dict]:
    conn = get_db()
    return [dict(r) for r in conn.execute("""
        SELECT r.id, r.title, b.slug AS book_slug, b.title AS book_title, bm.created_at
        FROM bookmarks bm
        JOIN recipes r ON r.id = bm.recipe_id
        JOIN books b ON b.id = r.book_id
        ORDER BY bm.created_at DESC
    """).fetchall()]

def toggle_bookmark(recipe_id: int) -> bool:
    conn = get_db()
    existing = conn.execute("SELECT id FROM bookmarks WHERE recipe_id = ?", (recipe_id,)).fetchone()
    if existing:
        conn.execute("DELETE FROM bookmarks WHERE recipe_id = ?", (recipe_id,))
        conn.commit()
        return False
    conn.execute("INSERT INTO bookmarks (recipe_id) VALUES (?)", (recipe_id,))
    conn.commit()
    return True

def is_bookmarked(recipe_id: int) -> bool:
    conn = get_db()
    return conn.execute("SELECT 1 FROM bookmarks WHERE recipe_id = ?", (recipe_id,)).fetchone() is not None

def get_all_ingredients() -> list[dict]:
    conn = get_db()
    return [dict(r) for r in conn.execute(
        "SELECT * FROM ingredient_index ORDER BY display_name"
    ).fetchall()]

def get_recipes_by_ingredient(name: str) -> list[dict]:
    conn = get_db()
    return [dict(r) for r in conn.execute("""
        SELECT r.id, r.title, r.page_start, b.slug AS book_slug, b.title AS book_title
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        JOIN books b ON b.id = r.book_id
        WHERE LOWER(ri.ingredient_name) = ?
        ORDER BY r.title
    """, (name.lower(),)).fetchall()]