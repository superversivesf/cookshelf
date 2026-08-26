import subprocess
import tempfile
from pathlib import Path


def extract_ebook_info(ebook_path: str) -> dict:
    """Extract title and author from a MOBI/EPUB file using ebook-meta."""
    info = {"title": None, "author": None, "page_count": 0, "pdf_version": None}
    try:
        result = subprocess.run(
            ["ebook-meta", ebook_path], capture_output=True, text=True, check=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Title:"):
                info["title"] = line[len("Title:"):].strip() or None
            elif line.startswith("Author(s):"):
                author = line[len("Author(s):"):].strip()
                if author:
                    info["author"] = author.split(",")[0].strip()
    except Exception:
        pass
    return info


def extract_ebook_text(ebook_path: str, cache_dir: Path) -> str:
    """Extract full text from a MOBI/EPUB file using ebook-convert."""
    slug = Path(ebook_path).stem
    cache_file = cache_dir / "text_cache" / slug / "0001.txt"
    if cache_file.exists():
        return cache_file.read_text()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_txt = tmp.name
    try:
        subprocess.run(
            ["ebook-convert", ebook_path, tmp_txt, "--txt-no-encoding-hack"],
            capture_output=True, text=True, check=True
        )
        text = Path(tmp_txt).read_text()
        cache_file.write_text(text)
        return text
    except Exception:
        return ""
    finally:
        Path(tmp_txt).unlink(missing_ok=True)