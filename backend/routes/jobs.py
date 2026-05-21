import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from db.session import get_db
from db.models import HRUser, TextLengthMixin
from services import job_service
from services.auth_service import get_current_user

router = APIRouter()


class JobIn(TextLengthMixin):
    title: str
    description: str | None = None
    deadline: datetime | None = None
    status: str = "draft"


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    deadline: datetime | None = None
    form_url: str | None = None
    published_platforms: list[str] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


@router.post("/", response_model=JobOut, status_code=201)
async def create_job(
    body: JobIn,
    db: AsyncSession = Depends(get_db),
    user: HRUser = Depends(get_current_user),
):
    return await job_service.create(
        db, body.title, body.description,
        deadline=body.deadline, status=body.status, created_by=user.id,
    )


@router.get("/", response_model=list[JobOut])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    return await job_service.list_all(db)


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    job = await job_service.get_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobOut)
async def update_job(
    job_id: uuid.UUID,
    body: JobIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    job = await job_service.get_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return await job_service.update(db, job, body.title, body.description, body.deadline, body.status)
