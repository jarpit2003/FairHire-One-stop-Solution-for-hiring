import asyncio
import sqlalchemy as sa
from db.session import init_engine
from config import settings


async def main():
    engine = init_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        r = await conn.execute(sa.text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name='form_submissions' ORDER BY ordinal_position"
        ))
        print("form_submissions columns:")
        for row in r:
            print(f"  {row[0]:25} {row[1]}")

        r2 = await conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='candidates' AND column_name='linkedin_url'"
        ))
        row2 = r2.fetchone()
        print(f"\ncandidates.linkedin_url: {'EXISTS' if row2 else 'MISSING'}")

        r3 = await conn.execute(sa.text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        ))
        print("\nAll tables:")
        for row in r3:
            print(f"  {row[0]}")

    await engine.dispose()


asyncio.run(main())
