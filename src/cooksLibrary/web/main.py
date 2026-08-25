from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routes.books import router as books_router
from .routes.recipes import router as recipes_router
from .routes.search import router as search_router
from .routes.ingredients import router as ingredients_router


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
    return app


app = create_app()
