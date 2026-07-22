from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.postgresql_database import (
    close_database_pool,
    initialize_database,
    open_database_pool,
)
from presentation.routes import router


@asynccontextmanager
async def lifespan(_app):
    open_database_pool()
    try:
        initialize_database()
        yield
    finally:
        close_database_pool()


def create_app():
    application = FastAPI(
        title="Media Monitoring API",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    application.include_router(router)
    return application


app = create_app()
