from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.post("/bookmarks")
def toggle_bookmark(request: Request, recipe_id: int = Form(...)):
    bookmarked = queries.toggle_bookmark(recipe_id)
    recipe = queries.get_recipe(recipe_id)
    return templates.TemplateResponse(request, "partials/bookmark_button.html", {
        "recipe": recipe, "bookmarked": bookmarked
    })


@router.delete("/bookmarks/{recipe_id}")
def remove_bookmark(recipe_id: int):
    queries.toggle_bookmark(recipe_id)
    return Response(status_code=204)


@router.get("/bookmarks")
def bookmarks_list(request: Request):
    bookmarks = queries.get_bookmarks()
    return templates.TemplateResponse(request, "bookmarks.html", {
        "bookmarks": bookmarks
    })