import subprocess
from pathlib import Path

def _cache_path(cache_dir: Path, pdf_path: str, page: int) -> Path:
    slug = Path(pdf_path).stem
    return cache_dir / "text_cache" / slug / f"{page:04d}.txt"

def extract_page(pdf_path: str, page_num: int, cache_dir: Path, force: bool = False) -> str:
    cache_file = _cache_path(cache_dir, pdf_path, page_num)
    if not force and cache_file.exists():
        return cache_file.read_text()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["pdftotext", "-f", str(page_num), "-l", str(page_num), "-layout",
         pdf_path, "-"],
        capture_output=True, text=True, check=True
    )
    cache_file.write_text(result.stdout)
    return result.stdout

def extract_pages(pdf_path: str, start: int, end: int, cache_dir: Path, force: bool = False) -> str:
    parts = [extract_page(pdf_path, p, cache_dir, force=force) for p in range(start, end + 1)]
    return "\n".join(parts)