import asyncio
import sys
import db.models  # registers all models into Base.metadata
from db.session import init_engine, Base
from config import settings

async def main():
    lines = []
    lines.append(f"DATABASE_URL: {settings.DATABASE_URL}")
    try:
        engine = init_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        tables = sorted(Base.metadata.tables.keys())
        lines.append(f"SUCCESS - tables created: {tables}")
        await engine.dispose()
    except Exception as e:
        lines.append(f"ERROR: {e}")

    result = "\n".join(lines)
    print(result)
    with open("init_db_result.txt", "w") as f:
        f.write(result + "\n")

asyncio.run(main())
