from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import get_settings, load_app_config
from app.core.logging import configure_logging
from app.core.scheduler import start_scheduler


def create_app() -> FastAPI:
    """애플리케이션을 생성하고 FastAPI를 설정"""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="VTC Link", version=settings.version)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(api_router)

    if settings.scheduler_enabled:
        config = load_app_config()
        start_scheduler(config)

    return app


app = create_app()
