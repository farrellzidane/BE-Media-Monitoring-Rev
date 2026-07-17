from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.sqlite_database import initialize_database
from presentation.routes import router


@asynccontextmanager
async def lifespan(_app):
    initialize_database()
    yield


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