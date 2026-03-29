"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import auth, projects


def create_app() -> FastAPI:
    init_db()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Admin-facing website generator for requirement polishing, design generation, and static site exports.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(auth.router)
    application.include_router(projects.router)
    return application


app = create_app()
