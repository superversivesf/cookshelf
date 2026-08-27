import argparse
import sqlite3
import sys
import re
from pathlib import Path
from ..config import get_settings
from ..db import connect, migrate
from .books import discover_books, compute_hash
from .categorize import load_categories, categorize_book
from .pdf_text import extract_page
from .detect import detect_recipes
from .section import section_recipe
from .confidence import score_recipe
from .index import rebuild_fts, rebuild_ingredient_index
from .ebook_text import extract_ebook_text, extract_ebook_cover

def run(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="cooksLibrary.ingest")
    parser.add_argument("--book", help="Re-ingest a specific book by slug")
    parser.add_argument("--force", action="store_true", help="Ignore cache and re-extract")
    parser.add_argument("--threshold", type=float, default=None, help="Confidence threshold")
    parser.add_argument("--llm-cleanup", action="store_true", help="Run LLM cleanup on low-confidence recipes")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    parser.add_argument("--max-recipes", type=int, default=0, help="Max recipes for LLM cleanup (0 = all)")
    opts = parser.parse_args(args)

    settings = get_settings()
    threshold = opts.threshold if opts.threshold is not None else settings.confidence_threshold
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

    conn = connect(settings.db_path)
    migrate(conn)

    if opts.llm_cleanup:
        from .llm_cleanup import run_cleanup
        return run_cleanup(conn, settings, opts.max_recipes, opts.dry_run)

    categories = load_categories(settings.categories_file) if Path(settings.categories_file).exists() else []
    books = discover_books(settings.library_path, conn)

    if opts.book and not any(b["slug"] == opts.book for b in books):
        row = conn.execute("SELECT * FROM books WHERE slug = ?", (opts.book,)).fetchone()
        if row:
            books.append(dict(row))

    for book in books:
        if opts.book and book["slug"] != opts.book:
            continue
        if book.get("is_ebook"):
            _ingest_ebook(conn, book, categories, settings, threshold)
        else:
            _ingest_book(conn, book, categories, settings, threshold, opts.force)

    rebuild_fts(conn)
    rebuild_ingredient_index(conn)
    conn.close()
    return 0

def _ingest_book(conn, book, categories, settings, threshold, force):
    pdf_path = book["source_path"]
    cache_dir = Path(settings.data_dir)
    # Derive category from first 5 pages of text
    early_text = ""
    for p in range(1, min(6, book["page_count"] + 1)):
        early_text += extract_page(pdf_path, p, cache_dir, force=force) + "\n"
    folder = Path(pdf_path).parent.name
    if categories:
        book["category"] = categorize_book(book, early_text, Path(pdf_path).name, folder, categories)
    else:
        book["category"] = "Uncategorized"

    existing_id = conn.execute(
        "SELECT id FROM books WHERE slug = ?", (book["slug"],)
    ).fetchone()
    book_id = existing_id[0] if existing_id else None
    if book_id is not None:
        conn.execute("DELETE FROM bookmarks WHERE recipe_id IN (SELECT id FROM recipes WHERE book_id = ?)", (book_id,))
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id IN (SELECT id FROM recipes WHERE book_id = ?)", (book_id,))
        conn.execute("DELETE FROM recipes WHERE book_id = ?", (book_id,))
    conn.execute("""
        INSERT OR REPLACE INTO books (id, slug, title, author, category, source_path, source_hash,
                          page_count, pdf_version, ingest_method, outline_present)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (book_id, book["slug"], book["title"], book["author"], book["category"],
          book["source_path"], book["source_hash"], book["page_count"],
          book["pdf_version"], "outline" if book["outline_present"] else "page-walk",
          int(book["outline_present"])))
    book_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Detect recipes
    recipes = detect_recipes(pdf_path, cache_dir, book["outline_present"], force=force)
    for rec in recipes:
        text = ""
        if rec["page_end"] and rec["page_end"] > rec["page_start"]:
            from .pdf_text import extract_pages
            text = extract_pages(pdf_path, rec["page_start"], rec["page_end"], cache_dir, force=force)
        else:
            text = extract_page(pdf_path, rec["page_start"], cache_dir, force=force)
        sectioned = section_recipe(text, rec["title"])
        score, notes = score_recipe({**sectioned, "title": rec["title"]})
        needs_review = 1 if score < threshold else 0
        render_method = "pdf_fallback" if needs_review else "structured"
        cursor = conn.execute("""
            INSERT OR IGNORE INTO recipes (book_id, title, page_start, page_end, description,
                                servings, servings_min, servings_max, instructions,
                                confidence, needs_review, render_method, extraction_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (book_id, rec["title"], rec["page_start"],
              rec["page_end"] if rec["page_end"] else None,
              sectioned["description"], sectioned["servings"],
              sectioned["servings_min"], sectioned["servings_max"],
              sectioned["instructions"], score, needs_review, render_method, notes))
        if cursor.rowcount == 0:
            continue
        recipe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for pos, ing in enumerate(sectioned["ingredients"]):
            parsed = ing.get("parsed", {})
            conn.execute("""
                INSERT INTO recipe_ingredients (recipe_id, position, section, quantity,
                                                unit, ingredient_name, note, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (recipe_id, pos, ing.get("section", ""), parsed.get("quantity"),
                  parsed.get("unit"), parsed.get("ingredient_name"),
                  parsed.get("note"), ing.get("line", "")))
    conn.commit()

def _ingest_ebook(conn, book, categories, settings, threshold):
    """Ingest a MOBI/EPUB ebook — extract full text and split into recipes."""
    ebook_path = book["source_path"]
    cache_dir = Path(settings.data_dir)
    extract_ebook_cover(ebook_path, book["slug"], cache_dir)
    full_text = extract_ebook_text(ebook_path, cache_dir)

    early_text = full_text[:2000]
    folder = Path(ebook_path).parent.name
    if categories:
        book["category"] = categorize_book(book, early_text, Path(ebook_path).name, folder, categories)
    else:
        book["category"] = "Uncategorized"

    existing_id = conn.execute("SELECT id FROM books WHERE slug = ?", (book["slug"],)).fetchone()
    book_id = existing_id[0] if existing_id else None
    if book_id is not None:
        conn.execute("DELETE FROM bookmarks WHERE recipe_id IN (SELECT id FROM recipes WHERE book_id = ?)", (book_id,))
        conn.execute("DELETE FROM made_recipes WHERE recipe_id IN (SELECT id FROM recipes WHERE book_id = ?)", (book_id,))
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id IN (SELECT id FROM recipes WHERE book_id = ?)", (book_id,))
        conn.execute("DELETE FROM recipes WHERE book_id = ?", (book_id,))
    conn.execute("""
        INSERT OR REPLACE INTO books (id, slug, title, author, category, source_path, source_hash,
                          page_count, pdf_version, ingest_method, outline_present)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (book_id, book["slug"], book["title"], book["author"], book["category"],
          book["source_path"], book["source_hash"], book["page_count"],
          book["pdf_version"], "ebook", 0))
    book_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    RECIPE_TITLE_RE = re.compile(
        r"^(?:[A-Z][A-Za-z0-9 ,'\-\u2019&/()]{3,80})\s*$", re.MULTILINE
    )
    SERVES_RE = re.compile(r"(?:SERVES|Serves|serves|MAKES|Makes)\s+(\d+)(?:\s*(?:to|-|\u2013)\s*(\d+))?",)

    matches = list(RECIPE_TITLE_RE.finditer(full_text))
    recipes = []
    for i, m in enumerate(matches):
        title = m.group(0).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        body = full_text[start:end].strip()
        if len(body) < 20:
            continue
        serves_match = SERVES_RE.search(body)
        if serves_match:
            s_min = int(serves_match.group(1))
            s_max = int(serves_match.group(2)) if serves_match.group(2) else s_min
            servings_str = serves_match.group(1)
        else:
            servings_str = None
            s_min = None
            s_max = None
        recipes.append({"title": title, "body": body, "servings": servings_str,
                        "servings_min": s_min, "servings_max": s_max})

    if not recipes:
        recipes.append({"title": book["title"], "body": full_text, "servings": None,
                        "servings_min": None, "servings_max": None})

    for idx, rec in enumerate(recipes):
        sectioned = section_recipe(rec["body"], rec["title"])
        sectioned["servings"] = rec["servings"]
        sectioned["servings_min"] = rec["servings_min"]
        sectioned["servings_max"] = rec["servings_max"]
        score, notes = score_recipe({**sectioned, "title": rec["title"]})
        needs_review = 1 if score < threshold else 0
        render_method = "pdf_fallback" if needs_review else "structured"
        conn.execute("""
            INSERT INTO recipes (book_id, title, page_start, page_end, description,
                                servings, servings_min, servings_max, instructions,
                                confidence, needs_review, render_method, extraction_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (book_id, rec["title"], idx + 1, None,
              sectioned["description"], rec["servings"],
              rec["servings_min"], rec["servings_max"],
              sectioned["instructions"], score, needs_review, render_method, "ebook"))
        recipe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for pos, ing in enumerate(sectioned["ingredients"]):
            parsed = ing.get("parsed", {})
            conn.execute("""
                INSERT INTO recipe_ingredients (recipe_id, position, section, quantity,
                                                unit, ingredient_name, note, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (recipe_id, pos, ing.get("section", ""), parsed.get("quantity"),
                  parsed.get("unit"), parsed.get("ingredient_name"),
                  parsed.get("note"), ing.get("line", "")))
    conn.commit()

def main():
    sys.exit(run(sys.argv[1:]))