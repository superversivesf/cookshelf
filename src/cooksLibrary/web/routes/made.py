from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/made")
def made_list(request: Request):
    made_recipes = queries.get_made_recipes()
    return templates.TemplateResponse(request, "made.html", {
        "made_recipes": made_recipes
    })


@router.post("/made")
def toggle_made(request: Request, recipe_id: int = Form(...)):
    made = queries.toggle_made(recipe_id)
    recipe = queries.get_recipe(recipe_id)
    return templates.TemplateResponse(request, "partials/made_button.html", {
        "recipe": recipe, "made": made
    })


@router.delete("/made/{recipe_id}")
def remove_made(recipe_id: int):
    queries.remove_made(recipe_id)
    return Response(status_code=204)