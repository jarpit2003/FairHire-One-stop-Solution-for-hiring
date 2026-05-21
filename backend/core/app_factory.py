from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from core.middleware import register_middleware
from core.routers import register_routers
from db.probe import probe_postgres
from db.session import Base, init_engine
import db.models  # noqa: F401 — register all ORM models before create_all

log = logging.getLogger(__name__)

_SQLITE_FALLBACK_URL = "sqlite+aiosqlite:///./fairhire.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    primary_url = settings.DATABASE_URL

    failure_reason = await probe_postgres(primary_url)
    if failure_reason is None:
        active_url = primary_url
        log.info("db: PostgreSQL connection verified — using %s", primary_url)
    else:
        active_url = _SQLITE_FALLBACK_URL
        log.warning(
            "db: PostgreSQL unavailable (%s) — "
            "falling back to SQLite (%s). "
            "Restore PostgreSQL credentials/server and restart to switch back.",
            failure_reason,
            _SQLITE_FALLBACK_URL,
        )

    resolved_engine = init_engine(active_url)
    async with resolved_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.JWT_SECRET == "CHANGE_ME_SET_JWT_SECRET_IN_DOT_ENV":
        raise RuntimeError(
            "JWT_SECRET is not set. "
            "Set a strong random secret in .env before starting the server."
        )
    if settings.SMTP_ENABLED and not settings.SMTP_USERNAME:
        log.warning("SMTP_ENABLED=true but SMTP_USERNAME is empty — emails will fail. Set SMTP credentials in .env.")

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="FairHire AI",
        description=(
            "Enterprise ATS-compliant hiring platform API. "
            "Provides candidate management, job postings, interview scheduling, "
            "resume uploads, and AI-powered embeddings."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={"name": "FairHire AI Team"},
        license_info={"name": "Proprietary"},
    )

    register_middleware(app)
    register_routers(app)

    return app
