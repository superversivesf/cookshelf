import sqlite3

def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM recipes_fts")
    rows = conn.execute("""
        SELECT r.id, r.title, r.description, r.instructions,
               GROUP_CONCAT(ri.ingredient_name, ' ') AS ingredient_names
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
        GROUP BY r.id
    """).fetchall()
    for row in rows:
        conn.execute(
            "INSERT INTO recipes_fts (rowid, title, description, instructions, ingredient_names) "
            "VALUES (?, ?, ?, ?, ?)",
            (row["id"], row["title"] or "", row["description"] or "",
             row["instructions"] or "", row["ingredient_names"] or "")
        )
    conn.commit()

def rebuild_ingredient_index(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM ingredient_index")
    rows = conn.execute("""
        SELECT LOWER(ingredient_name) AS name, COUNT(DISTINCT recipe_id) AS cnt
        FROM recipe_ingredients
        WHERE ingredient_name IS NOT NULL AND ingredient_name != ''
        GROUP BY LOWER(ingredient_name)
    """).fetchall()
    for row in rows:
        display = " ".join(w.capitalize() for w in row["name"].split())
        conn.execute(
            "INSERT OR IGNORE INTO ingredient_index (ingredient_name, display_name, recipe_count) "
            "VALUES (?, ?, ?)",
            (row["name"], display, row["cnt"])
        )
    conn.commit()