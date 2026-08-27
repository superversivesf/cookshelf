from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/pantry")
def pantry_page(request: Request):
    queries.import_pantry("")
    by_category = queries.get_pantry_by_category()
    return templates.TemplateResponse(request, "pantry.html", {
        "by_category": by_category
    })


@router.post("/pantry/toggle/{item_id}")
def toggle_pantry(request: Request, item_id: int):
    in_stock = queries.toggle_pantry_item(item_id)
    items = queries.get_pantry_items()
    item = None
    for it in items:
        if it["id"] == item_id:
            item = it
            break
    return templates.TemplateResponse(request, "partials/pantry_item.html", {
        "item": item or {"id": item_id, "ingredient_name": "", "category": "", "in_stock": in_stock}
    })