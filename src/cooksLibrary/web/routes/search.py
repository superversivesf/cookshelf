from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .. import queries

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/search")
def search(request: Request, q: str = "", type: str = "text"):
    results = []
    if q:
        results = queries.search_recipes(q)
    return templates.TemplateResponse(request, "search_results.html", {
        "query": q, "search_type": type, "results": results
    })