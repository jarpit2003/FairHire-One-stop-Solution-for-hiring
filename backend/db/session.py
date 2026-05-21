"""
db/session.py

Engine and session factory are intentionally NOT created at import time.
Call `init_engine(url)` once during application startup (lifespan) after
the DB probe has resolved which backend to use.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


# Module-level references populated by init_engine()
engine: AsyncEngine | None = None
_session_factory: sessionmaker | None = None


def init_engine(url: str) -> AsyncEngine:
    """
    Build and store the async engine + session factory for *url*.

    SQLite requires StaticPool and check_same_thread=False for async use.
    PostgreSQL uses the default pool (NullPool is fine for serverless, but
    the default AsyncAdaptedQueuePool works well for long-running processes).
    """
    global engine, _session_factory

    is_sqlite = url.startswith("sqlite")
    kwargs: dict = {"echo": False}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool

    engine = create_async_engine(url, **kwargs)
    _session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine


async def get_db() -> AsyncSession:  # type: ignore[return]
    if _session_factory is None:
        raise RuntimeError("Database engine has not been initialised. Call init_engine() first.")
    async with _session_factory() as session:
        yield session
