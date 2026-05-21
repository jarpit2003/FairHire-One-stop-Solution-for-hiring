"""
routes/intake.py

POST /api/v1/intake/submit
  Public endpoint (no auth) — called by Google Form webhook or any application form.
  Flow:
    1. Verify job exists
    2. Create/fetch Candidate
    3. Score resume against JD using existing AI matcher
    4. Create Application with resume_score persisted to DB
    5. Send acknowledgement email
"""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Job, Candidate, Application, FormSubmission
from services import candidate_service, application_service
from services.notification_service import send_application_acknowledgement
from services.profile_extractor import extract_profile
from services.jd_matcher import match_candidate_to_jd

router = APIRouter()


class IntakeSubmission(BaseModel):
    job_id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: str | None = None
    linkedin_url: str | None = None
    resume_text: str | None = None
    cover_note: str | None = None


class IntakeResponse(BaseModel):
    candidate_id: str
    application_id: str
    resume_score: float | None
    message: str
    email_sent: bool


@router.post("/submit", response_model=IntakeResponse, status_code=201)
async def intake_submit(
    body: IntakeSubmission,
    db: AsyncSession = Depends(get_db),
) -> IntakeResponse:
    job: Job | None = await db.get(Job, body.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build full resume text
    full_resume = "\n\n".join(filter(None, [
        body.resume_text,
        f"LinkedIn: {body.linkedin_url}" if body.linkedin_url else None,
        f"Cover Note: {body.cover_note}" if body.cover_note else None,
    ]))

    # Create or fetch candidate
    try:
        candidate = await candidate_service.create(
            db, full_name=body.full_name, email=body.email,
            resume_text=full_resume or None, phone=body.phone,
            linkedin_url=body.linkedin_url,
        )
    except Exception:
        result = await db.execute(select(Candidate).where(Candidate.email == body.email))
        candidate = result.scalar_one_or_none()
        if not candidate:
            raise

    # Check for duplicate application
    dup = await db.execute(
        select(Application).where(
            Application.job_id == body.job_id,
            Application.candidate_id == candidate.id,
        )
    )
    existing_app = dup.scalar_one_or_none()
    if existing_app:
        return IntakeResponse(
            candidate_id=str(candidate.id),
            application_id=str(existing_app.id),
            resume_score=existing_app.resume_score,
            message="Duplicate application — existing record returned.",
            email_sent=False,
        )

    # Score resume against JD
    resume_score: float | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []

    if full_resume and job.description:
        try:
            profile = extract_profile(full_resume)
            match = await match_candidate_to_jd(profile, job.description, full_resume)
            resume_score = float(match.fit_score)
            matched_skills = list(match.matched_skills)
            missing_skills = list(match.missing_skills)
        except Exception:
            pass  # score stays None — application still created

    # Persist Application
    app = await application_service.create(
        db,
        job_id=body.job_id,
        candidate_id=candidate.id,
        resume_score=resume_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )

    # Persist raw form submission — immutable audit record
    submission = FormSubmission(
        job_id=body.job_id,
        candidate_id=candidate.id,
        application_id=app.id,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        linkedin_url=body.linkedin_url,
        resume_text=body.resume_text,
        cover_note=body.cover_note,
        resume_score=resume_score,
        source="web_form",
    )
    db.add(submission)
    await db.commit()

    email_sent = await send_application_acknowledgement(
        candidate_email=candidate.email,
        candidate_name=candidate.full_name,
        job_title=job.title,
    )

    return IntakeResponse(
        candidate_id=str(candidate.id),
        application_id=str(app.id),
        resume_score=resume_score,
        message="Application received and scored.",
        email_sent=email_sent,
    )
