import subprocess
from pathlib import Path


def page_image_path(book_slug: str, page: int, data_dir: Path) -> Path:
    p = data_dir / "page_images" / book_slug / f"{page:04d}.webp"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def render_page(pdf_path: str, book_slug: str, page: int, data_dir: Path) -> Path | None:
    out_path = page_image_path(book_slug, page, data_dir)
    if out_path.exists():
        return out_path
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_png = tmp.name
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", "-f", str(page), "-l", str(page),
             pdf_path, tmp_png.rsplit(".", 1)[0]],
            check=True, capture_output=True
        )
        # pdftoppm appends page number to the prefix
        generated = f"{tmp_png.rsplit('.', 1)[0]}-{page:04d}.png"
        if not Path(generated).exists():
            generated = f"{tmp_png.rsplit('.', 1)[0]}-{page}.png"
        subprocess.run(["cwebp", "-quiet", generated, "-o", str(out_path)],
                       check=True, capture_output=True)
        Path(generated).unlink(missing_ok=True)
        return out_path
    except subprocess.CalledProcessError:
        return None
    finally:
        Path(tmp_png).unlink(missing_ok=True)