from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, events, forecast, ingest, paper_results, predict, regions
from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from seed_db import seed

    seed()
    yield


def create_app() -> FastAPI:
    """Create and configure the flood monitoring FastAPI application."""

    settings = get_settings()
    app = FastAPI(title="Flood Monitoring System", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(ingest.router)
    app.include_router(predict.router)
    app.include_router(forecast.router)
    app.include_router(events.router)
    app.include_router(alerts.router)
    app.include_router(regions.router)
    app.include_router(paper_results.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
