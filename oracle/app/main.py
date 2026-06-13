from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import orgs, events, artifacts, action_items, platform_links, auth, insights
from app.core.errors import register_error_handlers


@asynccontextmanager
async def lifespan(application: FastAPI):
    from app.api.deps import init_engine, dispose_engine
    settings = get_settings()
    await init_engine(settings.database_url)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Central AI Oracle — the connective tissue across all your platforms.",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(orgs.router, prefix="/orgs", tags=["Orgs"])
    app.include_router(events.router, prefix="/orgs/{org_id}/events", tags=["Events"])
    app.include_router(artifacts.router, prefix="/orgs/{org_id}/artifacts", tags=["Artifacts"])
    app.include_router(action_items.router, prefix="/orgs/{org_id}/action-items", tags=["Action Items"])
    app.include_router(platform_links.router, prefix="/orgs/{org_id}/platform-links", tags=["Platform Links"])
    app.include_router(insights.router, prefix="/orgs/{org_id}/insights", tags=["Insights"])

    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok", "service": "nexus-oracle", "version": "0.2.0"}

    return app


app = create_app()
