import hashlib
import re
import sqlite3
from pathlib import Path
import pypdf
import wordsegment
from .pdf_info import extract_info
from .ebook_text import extract_ebook_info

EBOOK_EXTENSIONS = {".mobi", ".epub", ".azw", ".azw3"}

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

def compute_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def discover_books(library_paths: list[str], conn: sqlite3.Connection) -> list[dict]:
    books = []
    for lib_path in library_paths:
        lib = Path(lib_path)
        files = sorted(list(lib.rglob("*.pdf")) +
                       [p for p in lib.rglob("*") if p.suffix.lower() in EBOOK_EXTENSIONS])
        for file_path in files:
            source_hash = compute_hash(str(file_path))
            existing = conn.execute(
                "SELECT id FROM books WHERE source_hash = ?", (source_hash,)
            ).fetchone()
            if existing:
                continue
            is_ebook = file_path.suffix.lower() in EBOOK_EXTENSIONS
            try:
                if is_ebook:
                    info = extract_ebook_info(str(file_path))
                    outline_present = False
                else:
                    info = extract_info(str(file_path))
                    outline_present = _has_outline(str(file_path))
            except Exception:
                print(f"  Skipping {file_path.name}: extraction failed")
                continue
            title = info["title"] or prettify_filename(file_path.name)
            slug = make_slug(title)
            books.append({
                "slug": slug, "title": title, "author": info["author"],
                "source_path": str(file_path), "source_hash": source_hash,
                "page_count": info["page_count"], "pdf_version": info["pdf_version"],
                "outline_present": outline_present,
                "is_ebook": is_ebook,
            })
    return books

def _has_outline(pdf_path: str) -> bool:
    try:
        reader = pypdf.PdfReader(pdf_path)
        return bool(reader.outline)
    except Exception:
        return False
