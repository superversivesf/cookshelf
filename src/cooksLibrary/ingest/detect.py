import re
import pypdf
from pathlib import Path
from .pdf_text import extract_page

STOPLIST_RE = re.compile(
    r"^(cover|title|copyright|contents|index|acknowledg?ments?|credits?|"
    r"introduction|foreword|preface|about the author|chronicle ebooks?|"
    r"how to\s|recipes$)",
    re.IGNORECASE,
)

SERVES_RE = re.compile(r"(?:SERVES|Serves|serves|MAKES|Makes)\s+(\d+)(?:\s*(?:to|-|\u2013)\s*(\d+))?",)

def filter_outline_entries(entries: list[tuple[str, int]]) -> list[tuple[str, int]]:
    return [(t, p) for t, p in entries
            if not STOPLIST_RE.match(t.strip()) and len(t.strip()) >= 2]

def _flatten_outline(reader: pypdf.PdfReader) -> list[tuple[str, int]]:
    result = []
    def walk(items):
        for item in items:
            if isinstance(item, list):
                walk(item)
            else:
                try:
                    page = reader.get_destination_page_number(item)
                    result.append((item.title, page))
                except Exception:
                    pass
    walk(reader.outline)
    return result

def _detect_outline(pdf_path: str) -> list[dict]:
    reader = pypdf.PdfReader(pdf_path)
    entries = _flatten_outline(reader)
    entries = filter_outline_entries(entries)
    if len(entries) < 5:
        return []
    recipes = []
    for i, (title, page) in enumerate(entries):
        next_page = entries[i + 1][1] - 1 if i + 1 < len(entries) else len(reader.pages) - 1
        page_end = page if next_page < page else next_page
        recipes.append({"title": title, "page_start": page + 1, "page_end": page_end + 1,
                        "ingest_method": "outline"})
    return recipes

def _detect_page_walk(pdf_path: str, cache_dir: Path, force: bool = False) -> list[dict]:
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    recipes = []
    current_start = None
    current_title = None
    for p in range(1, total_pages + 1):
        text = extract_page(pdf_path, p, cache_dir, force=force)
        is_recipe_start = _is_recipe_start(text)
        if is_recipe_start:
            if current_start is not None:
                recipes.append({
                    "title": current_title,
                    "page_start": current_start, "page_end": p - 1,
                    "ingest_method": "page-walk"
                })
            current_start = p
            current_title = _extract_title(text)
    if current_start is not None:
        recipes.append({
            "title": current_title, "page_start": current_start, "page_end": total_pages,
            "ingest_method": "page-walk"
        })
    return recipes

def _is_recipe_start(text: str) -> bool:
    has_serves = bool(SERVES_RE.search(text))
    lines = [l for l in text.strip().splitlines() if l.strip()]
    has_short_title = bool(lines and len(lines[0].strip()) < 60)
    return has_serves and has_short_title

def _extract_title(text: str) -> str:
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return lines[0].strip() if lines else ""

def detect_recipes(pdf_path: str, cache_dir: Path, outline_present: bool, force: bool = False) -> list[dict]:
    if outline_present:
        outline_recipes = _detect_outline(pdf_path)
        if len(outline_recipes) >= 5:
            return outline_recipes
    return _detect_page_walk(pdf_path, cache_dir, force=force)