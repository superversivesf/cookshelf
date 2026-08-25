import argparse
import sqlite3
import sys
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

    for book in books:
        if opts.book and book["slug"] != opts.book:
            continue
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
        early_text += extract_page(pdf_path, p, cache_dir) + "\n"
    folder = Path(pdf_path).parent.name
    if categories:
        book["category"] = categorize_book(book, early_text, Path(pdf_path).name, folder, categories)
    else:
        book["category"] = "Uncategorized"

    # Insert book
    conn.execute("""
        INSERT INTO books (slug, title, author, category, source_path, source_hash,
                          page_count, pdf_version, ingest_method, outline_present)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (book["slug"], book["title"], book["author"], book["category"],
          book["source_path"], book["source_hash"], book["page_count"],
          book["pdf_version"], "outline" if book["outline_present"] else "page-walk",
          int(book["outline_present"])))
    book_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Detect recipes
    recipes = detect_recipes(pdf_path, cache_dir, book["outline_present"])
    for rec in recipes:
        text = ""
        if rec["page_end"] and rec["page_end"] > rec["page_start"]:
            from .pdf_text import extract_pages
            text = extract_pages(pdf_path, rec["page_start"] + 1, rec["page_end"] + 1, cache_dir)
        else:
            text = extract_page(pdf_path, rec["page_start"] + 1, cache_dir)
        sectioned = section_recipe(text, rec["title"])
        score, notes = score_recipe({**sectioned, "title": rec["title"]})
        needs_review = 1 if score < threshold else 0
        render_method = "pdf_fallback" if needs_review else "structured"
        conn.execute("""
            INSERT INTO recipes (book_id, title, page_start, page_end, description,
                                servings, servings_min, servings_max, instructions,
                                confidence, needs_review, render_method, extraction_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (book_id, rec["title"], rec["page_start"] + 1,
              (rec["page_end"] + 1) if rec["page_end"] else None,
              sectioned["description"], sectioned["servings"],
              sectioned["servings_min"], sectioned["servings_max"],
              sectioned["instructions"], score, needs_review, render_method, notes))
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