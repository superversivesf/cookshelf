from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/books")
def book_list(request: Request):
    books = queries.get_books_by_category()
    by_category = {}
    for b in books:
        by_category.setdefault(b.get("category") or "Uncategorized", []).append(b)
    return templates.TemplateResponse(request, "book_list.html", {
        "by_category": by_category
    })

@router.get("/books/{slug}")
def book_detail(request: Request, slug: str):
    book = queries.get_book_by_slug(slug)
    if not book:
        return templates.TemplateResponse(request, "404.html", {}, status_code=404)
    recipes = queries.get_recipes_for_book(book["id"])
    return templates.TemplateResponse(request, "book_detail.html", {
        "book": book, "recipes": recipes
    })