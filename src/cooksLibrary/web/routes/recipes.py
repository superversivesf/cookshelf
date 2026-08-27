from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/recipes/{recipe_id}")
def recipe_view(request: Request, recipe_id: int):
    recipe = queries.get_recipe(recipe_id)
    if not recipe:
        return templates.TemplateResponse(request, "404.html", {}, status_code=404)
    book = (
        queries.get_book_by_slug(recipe["book_slug"]) if "book_slug" in recipe else None
    )
    if not book:
        book_row = (
            queries.get_db()
            .execute("SELECT * FROM books WHERE id = ?", (recipe["book_id"],))
            .fetchone()
        )
        book = dict(book_row) if book_row else None
    bookmarked = queries.is_bookmarked(recipe_id)
    made = queries.is_made(recipe_id)
    shopping_items = queries.get_shopping_list()
    on_list = any(item["recipe_id"] == recipe_id for item in shopping_items)
    is_ebook = book and book.get("ingest_method") == "ebook"
    template_name = (
        "recipe_fallback.html"
        if recipe["render_method"] == "pdf_fallback"
        else "recipe.html"
    )
    return templates.TemplateResponse(
        request,
        template_name,
        {"recipe": recipe, "book": book, "bookmarked": bookmarked, "made": made, "on_list": on_list, "is_ebook": is_ebook},
    )
