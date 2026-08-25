from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/ingredients")
def ingredient_list(request: Request):
    ingredients = queries.get_all_ingredients()
    return templates.TemplateResponse(request, "ingredient_list.html", {
        "ingredients": ingredients
    })

@router.get("/ingredients/{name}")
def ingredient_detail(request: Request, name: str):
    recipes = queries.get_recipes_by_ingredient(name)
    return templates.TemplateResponse(request, "ingredient_detail.html", {
        "ingredient_name": name, "recipes": recipes
    })