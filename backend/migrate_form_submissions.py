"""
migrate_form_submissions.py

Adds:
  - candidates.linkedin_url  (VARCHAR 1000, nullable)
  - form_submissions table   (raw audit log of every apply/intake submission)

Safe to run multiple times — uses IF NOT EXISTS / IF NOT EXISTS guards.
"""
import asyncio
from db.session import init_engine, Base
from config import settings
import db.models  # registers all models


async def main():
    engine = init_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Add linkedin_url column to candidates if missing
        await conn.execute(__import__("sqlalchemy").text(
            "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(1000)"
        ))
        print("[OK] candidates.linkedin_url ensured")

        # Create form_submissions table from metadata (no-op if already exists)
        await conn.run_sync(
            lambda sync_conn: Base.metadata.tables["form_submissions"].create(
                sync_conn, checkfirst=True
            )
        )
        print("[OK] form_submissions table ensured")

    await engine.dispose()
    print("Migration complete.")


asyncio.run(main())
