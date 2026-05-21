import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Job


async def create(
    db: AsyncSession,
    title: str,
    description: str | None,
    deadline: datetime | None = None,
    status: str = "draft",
    created_by: uuid.UUID | None = None,
) -> Job:
    job = Job(
        title=title,
        description=description,
        deadline=deadline,
        status=status,
        created_by=created_by,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update(
    db: AsyncSession,
    job: Job,
    title: str,
    description: str | None,
    deadline: datetime | None = None,
    status: str | None = None,
) -> Job:
    job.title = title
    job.description = description
    if deadline is not None:
        job.deadline = deadline
    if status is not None:
        job.status = status
    await db.commit()
    await db.refresh(job)
    return job


async def list_all(db: AsyncSession) -> list[Job]:
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    return await db.get(Job, job_id)
