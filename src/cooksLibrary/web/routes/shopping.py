from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/shopping")
def shopping_list(request: Request):
    items = queries.get_shopping_list()
    recipe_title = items[0]["recipe_title"] if items else None
    recipe_id = items[0]["recipe_id"] if items else None
    return templates.TemplateResponse(request, "shopping.html", {
        "items": items,
        "recipe_title": recipe_title,
        "recipe_id": recipe_id,
    })


@router.post("/shopping/add/{recipe_id}")
def add_to_shopping_list(recipe_id: int):
    queries.add_recipe_to_shopping_list(recipe_id)
    return RedirectResponse(url="/shopping", status_code=303)


@router.post("/shopping/toggle/{item_id}")
def toggle_item(request: Request, item_id: int):
    checked = queries.toggle_shopping_list_item(item_id)
    item = None
    items = queries.get_shopping_list()
    for it in items:
        if it["id"] == item_id:
            item = it
            break
    return templates.TemplateResponse(request, "partials/shopping_list_row.html", {
        "item": item or {"id": item_id, "ingredient_text": "", "checked": checked, "recipe_id": 0, "recipe_title": ""}
    })


@router.post("/shopping/clear")
def clear_list(request: Request):
    queries.clear_shopping_list()
    items = queries.get_shopping_list()
    return templates.TemplateResponse(request, "partials/shopping_list_items.html", {
        "items": items, "recipe_title": None, "recipe_id": None
    })