"""
routes/interviews.py

POST  /api/v1/interviews                    — schedule interview
GET   /api/v1/interviews?job_id=            — list (filter by job)
PATCH /api/v1/interviews/{id}/score         — interviewer submits score → updates Application
PATCH /api/v1/interviews/{id}/status        — mark completed/cancelled
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Interview, Candidate, Job, HRUser, TextLengthMixin
from services import interview_service, application_service
from services.auth_service import get_current_user
from services.notification_service import send_interview_confirmation, send_interviewer_notification

router = APIRouter()


class InterviewIn(TextLengthMixin):
    candidate_id: str
    job_id: str
    application_id: str | None = None
    round_number: int = 1
    interviewer_id: str | None = None
    status: str = "scheduled"
    scheduled_at: datetime | None = None
    meet_link: str | None = None
    notes: str | None = None


class InterviewOut(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    application_id: str | None
    round_number: int
    interviewer_name: str | None
    status: str
    scheduled_at: datetime | None
    meet_link: str | None
    notes: str | None
    score: float | None
    feedback: str | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_safe(cls, obj: "Interview") -> "InterviewOut":
        return cls(
            id=str(obj.id),
            candidate_id=str(obj.candidate_id),
            job_id=str(obj.job_id),
            application_id=str(obj.application_id) if obj.application_id else None,
            round_number=obj.round_number,
            interviewer_name=obj.interviewer_name,
            status=obj.status,
            scheduled_at=obj.scheduled_at,
            meet_link=obj.meet_link,
            notes=obj.notes,
            score=obj.score,
            feedback=obj.feedback,
        )


class ScoreIn(BaseModel):
    score: float
    feedback: str | None = None


class StatusIn(BaseModel):
    status: str


@router.post("/", response_model=InterviewOut, status_code=201)
async def create_interview(
    body: InterviewIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    try:
        cand_uuid = uuid.UUID(body.candidate_id)
        job_uuid = uuid.UUID(body.job_id)
        app_uuid = uuid.UUID(body.application_id) if body.application_id else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")

    interview = await interview_service.create(
        db,
        candidate_id=cand_uuid,
        job_id=job_uuid,
        application_id=app_uuid,
        round_number=body.round_number,
        interviewer_name=body.interviewer_id,
        status=body.status,
        scheduled_at=body.scheduled_at,
        meet_link=body.meet_link,
        notes=body.notes,
    )

    try:
        candidate: Candidate | None = await db.get(Candidate, cand_uuid)
        job: Job | None = await db.get(Job, job_uuid)
    except Exception:
        candidate = None
        job = None

    if candidate and job and body.scheduled_at:
        # Check if interview confirmation already sent for this candidate+job+round
        from sqlalchemy import select as _select
        existing = await db.execute(
            _select(Interview).where(
                Interview.candidate_id == cand_uuid,
                Interview.job_id == job_uuid,
                Interview.round_number == body.round_number,
                Interview.id != interview.id,
            ).limit(1)
        )
        already_scheduled = existing.scalars().first() is not None
        if not already_scheduled:
            await send_interview_confirmation(
                candidate_email=candidate.email,
                candidate_name=candidate.full_name,
                job_title=job.title,
                interview_date=body.scheduled_at.strftime("%B %d, %Y"),
                interview_time=body.scheduled_at.strftime("%I:%M %p"),
                meet_link=body.meet_link,
                notes=body.notes,
            )

    return InterviewOut.from_orm_safe(interview)


@router.get("/", response_model=list[InterviewOut])
async def list_interviews(
    job_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    if job_id:
        try:
            jid = uuid.UUID(job_id)
            interviews = await interview_service.list_by_job(db, jid, limit=limit, offset=offset)
        except ValueError:
            interviews = await interview_service.list_all(db, limit=limit, offset=offset)
    else:
        interviews = await interview_service.list_all(db, limit=limit, offset=offset)
    return [InterviewOut.from_orm_safe(i) for i in interviews]


@router.patch("/{interview_id}/score", response_model=InterviewOut)
async def submit_score(
    interview_id: str,
    body: ScoreIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    try:
        iid = uuid.UUID(interview_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    interview: Interview | None = await db.get(Interview, iid)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    interview.score = body.score
    interview.feedback = body.feedback
    interview.status = "completed"
    await db.commit()
    await db.refresh(interview)

    if interview.application_id:
        app = await application_service.get_by_id(db, uuid.UUID(str(interview.application_id)))
        if app:
            await application_service.record_interview_score(
                db, app, body.score, interview.round_number
            )

    return InterviewOut.from_orm_safe(interview)


@router.patch("/{interview_id}/status", response_model=InterviewOut)
async def update_status(
    interview_id: str,
    body: StatusIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
):
    try:
        iid = uuid.UUID(interview_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    interview: Interview | None = await db.get(Interview, iid)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    interview.status = body.status
    await db.commit()
    await db.refresh(interview)
    return InterviewOut.from_orm_safe(interview)
