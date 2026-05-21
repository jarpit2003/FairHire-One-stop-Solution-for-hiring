import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from services import candidate_service
from services.auth_service import get_current_user
from db.models import HRUser
from services.notification_service import send_application_acknowledgement

router = APIRouter()


class CandidateIn(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    resume_text: str | None = None
    job_title: str | None = None


class CandidateOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None
    resume_text: str | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=CandidateOut, status_code=201)
async def create_candidate(body: CandidateIn, db: AsyncSession = Depends(get_db)):
    candidate, created = await candidate_service.get_or_create(
        db, body.full_name, body.email, body.resume_text, body.phone
    )
    if created and body.job_title:
        await send_application_acknowledgement(
            candidate_email=candidate.email,
            candidate_name=candidate.full_name,
            job_title=body.job_title,
        )
    return candidate


@router.get("/", response_model=list[CandidateOut])
async def list_candidates(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    return await candidate_service.list_all(db, limit=limit, offset=offset)


@router.get("/{candidate_id}", response_model=CandidateOut)
async def get_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    candidate = await candidate_service.get_by_id(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
