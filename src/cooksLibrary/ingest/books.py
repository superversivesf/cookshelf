import hashlib
import re
import sqlite3
from pathlib import Path
import pypdf
import wordsegment
from .pdf_info import extract_info

wordsegment.load()

def make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug

def prettify_filename(filename: str) -> str:
    base = Path(filename).stem
    base = base.replace("_", " ")
    pieces = []
    for piece in base.split():
        segmented = wordsegment.segment(piece)
        if segmented:
            pieces.extend(segmented)
        else:
            pieces.append(piece)
    return " ".join(w.capitalize() for w in pieces)

def compute_hash(pdf_path: str) -> str:
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def discover_books(library_paths: list[str], conn: sqlite3.Connection) -> list[dict]:
    books = []
    for lib_path in library_paths:
        for pdf_path in sorted(Path(lib_path).rglob("*.pdf")):
            source_hash = compute_hash(str(pdf_path))
            existing = conn.execute(
                "SELECT id FROM books WHERE source_hash = ?", (source_hash,)
            ).fetchone()
            if existing:
                continue
            info = extract_info(str(pdf_path))
            title = info["title"] or prettify_filename(pdf_path.name)
            slug = make_slug(title)
            outline_present = _has_outline(str(pdf_path))
            books.append({
                "slug": slug, "title": title, "author": info["author"],
                "source_path": str(pdf_path), "source_hash": source_hash,
                "page_count": info["page_count"], "pdf_version": info["pdf_version"],
                "outline_present": outline_present,
            })
    return books

def _has_outline(pdf_path: str) -> bool:
    try:
        reader = pypdf.PdfReader(pdf_path)
        return bool(reader.outline)
    except Exception:
        return False