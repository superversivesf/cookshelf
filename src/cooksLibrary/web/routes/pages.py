from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
from .. import queries
from ...config import get_settings
from ...ingest.images import render_page

router = APIRouter()


@router.get("/books/{slug}/page/{page}")
def page_image(slug: str, page: int):
    book = queries.get_book_by_slug(slug)
    if not book:
        return FileResponse(status_code=404)
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    from ...ingest.images import page_image_path
    img_path = page_image_path(slug, page, data_dir)
    if not img_path.exists():
        img_path = render_page(book["source_path"], slug, page, data_dir)
        if not img_path:
            return FileResponse(status_code=404)
    return FileResponse(str(img_path), media_type="image/webp",
                        headers={"Cache-Control": "max-age=31536000"})