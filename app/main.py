from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.modules.notifications.scheduler import (
    start_notification_scheduler,
    stop_notification_scheduler,
)


def init_sentry(app_settings: Settings = settings) -> None:
    if not app_settings.SENTRY_DSN:
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=app_settings.SENTRY_DSN,
        environment=app_settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=app_settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    scheduler_task = start_notification_scheduler()
    try:
        yield
    finally:
        await stop_notification_scheduler(scheduler_task)


def create_app() -> FastAPI:
    init_sentry()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Backend for a driver assistant app: auth, vehicles, trips, "
            "balance, notifications, recommendations, and ML adapters."
        ),
        servers=[{"url": "/", "description": "Current API host"}],
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Health"])
    async def root() -> dict[str, str]:
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
