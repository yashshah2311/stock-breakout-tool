from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings
from app.db.repository import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    init_db(settings.database_url)

    app = FastAPI(
        title="Stock Breakout Tool",
        version="0.1.0",
        description="Data-driven Zerodha + OpenAI stock breakout scanner.",
    )

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(settings.project_root / "app" / "static" / "index.html")

    app.mount("/static", StaticFiles(directory=settings.project_root / "app" / "static"), name="static")
    app.include_router(router)
    return app


app = create_app()
