from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.logging import configure_logging
from app.core.request_id import RequestIdMiddleware
from app.core.errors import AppError
from app.core.config import get_settings


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        from app.db.local import initialize_sqlite_database

        initialize_sqlite_database(settings.database_url)
    app = FastAPI(title="FashionRAG API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "request_id": request_id,
                "code": exc.code,
                "message": exc.message,
                "data": None,
            },
        )

    app.include_router(api_router)
    return app
