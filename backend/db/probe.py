"""
db/probe.py — real SQLAlchemy connectivity + authentication probe.

Creates a throw-away async engine with NullPool (no persistent connections),
attempts one no-op transaction, then disposes the engine immediately.
Returns None on success, or the str(exception) as the failure reason so the
caller can log exactly why the fallback was triggered.
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

log = logging.getLogger(__name__)


async def probe_postgres(url: str) -> str | None:
    """
    Try to open a real connection to *url*.

    Returns:
        None              — connection and authentication succeeded.
        str (reason)      — any failure: network, auth, driver, etc.
    """
    test_engine = create_async_engine(url, poolclass=NullPool, echo=False)
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        return None
    except Exception as exc:
        return str(exc)
    finally:
        await test_engine.dispose()
