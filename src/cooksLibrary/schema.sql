CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    category TEXT,
    category_override TEXT,
    source_path TEXT NOT NULL,
    source_hash TEXT UNIQUE NOT NULL,
    page_count INTEGER NOT NULL,
    pdf_version TEXT,
    ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
    ingest_method TEXT,
    outline_present INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    title TEXT NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER,
    description TEXT,
    servings TEXT,
    servings_min INTEGER,
    servings_max INTEGER,
    instructions TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    needs_review INTEGER NOT NULL DEFAULT 0,
    render_method TEXT NOT NULL DEFAULT 'structured',
    extraction_notes TEXT,
    UNIQUE(book_id, page_start)
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    position INTEGER NOT NULL,
    section TEXT NOT NULL DEFAULT '',
    quantity TEXT,
    quantity_norm REAL,
    unit TEXT,
    ingredient_name TEXT,
    note TEXT,
    raw_text TEXT NOT NULL,
    UNIQUE(recipe_id, position)
);

CREATE TABLE IF NOT EXISTS ingredient_index (
    ingredient_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    recipe_count INTEGER NOT NULL DEFAULT 0,
    aliases TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL UNIQUE REFERENCES recipes(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    note TEXT
);

CREATE TABLE IF NOT EXISTS made_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL UNIQUE REFERENCES recipes(id),
    made_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    recipe_title TEXT NOT NULL,
    ingredient_text TEXT NOT NULL,
    checked INTEGER NOT NULL DEFAULT 0,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts USING fts5(
    title, description, instructions, ingredient_names
);
CREATE TABLE IF NOT EXISTS pantry_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'other',
    in_stock INTEGER NOT NULL DEFAULT 0
);
