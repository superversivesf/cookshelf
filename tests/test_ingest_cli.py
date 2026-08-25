import os
import sqlite3
from pathlib import Path
from cooksLibrary.ingest.cli import run
from cooksLibrary.db import connect, migrate

REAL_PDF_DIR = "/mnt/media/Komga/Cooking/Weekend Cooking/eatlikeamanguidetofeedingacrowd.pdf"
REAL_AVAILABLE = os.path.exists(REAL_PDF_DIR)

import pytest

@pytest.mark.skipif(not REAL_AVAILABLE, reason="Test PDFs not mounted")
def test_ingest_one_book(tmp_data_dir, monkeypatch):
    db_path = str(tmp_data_dir / "test.db")
    lib_dir = os.path.dirname(REAL_PDF_DIR)
    monkeypatch.setenv("COOKS_LIBRARY_PATH", lib_dir)
    monkeypatch.setenv("COOKS_DB_PATH", db_path)
    monkeypatch.setenv("COOKS_DATA_DIR", str(tmp_data_dir))
    monkeypatch.setenv("COOKS_CATEGORIES_FILE", str(Path(__file__).parent.parent / "categories.yml"))
    exit_code = run(["--book", "the-eat-like-a-man-guide-to-feeding-a-crowd"])
    assert exit_code == 0
    conn = connect(db_path)
    migrate(conn)
    count = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    assert count > 5
    books = conn.execute("SELECT title, category FROM books").fetchall()
    assert len(books) == 1
    conn.close()