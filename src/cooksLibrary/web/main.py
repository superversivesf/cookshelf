from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routes.books import router as books_router
from .routes.recipes import router as recipes_router
from .routes.search import router as search_router
from .routes.ingredients import router as ingredients_router
from .routes.bookmarks import router as bookmarks_router
from .routes.made import router as made_router
from .routes.pages import router as pages_router
from .routes.shopping import router as shopping_router
from .routes.pantry import router as pantry_router


def create_app() -> FastAPI:
    app = FastAPI(title="Cook's Library")
    base_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=str(base_dir / "templates"))
    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def home(request: Request):
        return templates.TemplateResponse(request, "home.html")

    app.include_router(books_router)
    app.include_router(recipes_router)
    app.include_router(search_router)
    app.include_router(ingredients_router)
    app.include_router(bookmarks_router)
    app.include_router(made_router)
    app.include_router(pages_router)
    app.include_router(shopping_router)
    app.include_router(pantry_router)
    return app


app = create_app()
