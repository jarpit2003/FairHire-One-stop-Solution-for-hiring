"""
routes/applications.py

GET    /api/v1/applications?job_id=          — ranked list for a job
POST   /api/v1/applications                  — create (called by intake)
GET    /api/v1/applications/{id}             — single application detail
PATCH  /api/v1/applications/{id}/stage       — advance pipeline stage
POST   /api/v1/applications/{id}/test-score  — record assessment result
POST   /api/v1/applications/{id}/reject      — reject + send email
POST   /api/v1/applications/{id}/offer       — make offer + send email
"""
from __future__ import annotations

import csv
import io
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Application, Candidate, Job, TextLengthMixin
from services import application_service
from services.auth_service import get_current_user
from services.notification_service import send_rejection, send_offer, send_test_link
from services.offer_service import draft_offer_email
from db.models import HRUser
from config import settings

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ApplicationOut(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str | None
    resume_score: float | None
    test_score: float | None
    interview_score: float | None
    hr_interview_score: float | None
    final_score: float | None
    # Score component breakdown
    score_impact: float | None = None
    score_semantic: float | None = None
    score_skill: float | None = None
    score_cert: float | None = None
    score_experience: float | None = None
    resume_quality_score: int | None = None
    stage: str
    status: str
    rejection_reason: str | None = None
    matched_skills: list[str]
    missing_skills: list[str]
    applied_at: str
    resume_weight: int
    test_weight: int
    email_sent: bool = False
    email_status: str = ""


class CreateApplicationIn(TextLengthMixin):
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    resume_score: float | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class StageIn(BaseModel):
    stage: str
    rejection_reason: str | None = None


class TestScoreIn(BaseModel):
    test_score: float


class SendTestLinkIn(BaseModel):
    test_link: str
    deadline: str | None = None


class WeightsIn(BaseModel):
    resume_weight: int
    test_weight: int


class OfferDraftOut(BaseModel):
    draft: str
    candidate_name: str
    job_title: str


class SendOfferIn(BaseModel):
    draft: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _enrich_many(db: AsyncSession, apps: list[Application]) -> list[ApplicationOut]:
    """Batch-load all candidates in one query — eliminates N+1."""
    if not apps:
        return []
    candidate_ids = list({a.candidate_id for a in apps})
    result = await db.execute(select(Candidate).where(Candidate.id.in_(candidate_ids)))
    cand_map: dict[uuid.UUID, Candidate] = {c.id: c for c in result.scalars().all()}
    out = []
    for a in apps:
        c = cand_map.get(a.candidate_id)
        out.append(ApplicationOut(
            id=str(a.id), job_id=str(a.job_id), candidate_id=str(a.candidate_id),
            candidate_name=c.full_name if c else "Unknown",
            candidate_email=c.email if c else "",
            candidate_phone=c.phone if c else None,
            resume_score=a.resume_score, test_score=a.test_score,
            interview_score=a.interview_score, hr_interview_score=a.hr_interview_score,
            final_score=a.final_score, stage=a.stage, status=a.status,
            score_impact=a.score_impact, score_semantic=a.score_semantic,
            score_skill=a.score_skill, score_cert=a.score_cert,
            score_experience=a.score_experience,
            resume_quality_score=a.resume_quality_score,
            rejection_reason=a.rejection_reason,
            matched_skills=a.matched_skills or [], missing_skills=a.missing_skills or [],
            applied_at=a.applied_at.isoformat(),
            resume_weight=a.resume_weight, test_weight=a.test_weight,
        ))
    return out


async def _enrich(db: AsyncSession, app: Application, email_sent: bool = False, email_status: str = "") -> ApplicationOut:
    candidate: Candidate | None = await db.get(Candidate, app.candidate_id)
    return ApplicationOut(
        id=str(app.id), job_id=str(app.job_id), candidate_id=str(app.candidate_id),
        candidate_name=candidate.full_name if candidate else "Unknown",
        candidate_email=candidate.email if candidate else "",
        candidate_phone=candidate.phone if candidate else None,
        resume_score=app.resume_score, test_score=app.test_score,
        interview_score=app.interview_score, hr_interview_score=app.hr_interview_score,
        final_score=app.final_score, stage=app.stage, status=app.status,
        score_impact=app.score_impact, score_semantic=app.score_semantic,
        score_skill=app.score_skill, score_cert=app.score_cert,
        score_experience=app.score_experience,
        resume_quality_score=app.resume_quality_score,
        rejection_reason=app.rejection_reason,
        matched_skills=app.matched_skills or [], missing_skills=app.missing_skills or [],
        applied_at=app.applied_at.isoformat(),
        resume_weight=app.resume_weight, test_weight=app.test_weight,
        email_sent=email_sent, email_status=email_status,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ApplicationOut])
async def list_applications(
    job_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    stage: str | None = Query(None, description="Filter by stage"),
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> list[ApplicationOut]:
    apps = await application_service.list_by_job(db, job_id, limit=limit, offset=offset, stage=stage)
    return await _enrich_many(db, apps)


@router.get("/shortlist", response_model=list[ApplicationOut])
async def get_shortlist(
    job_id: uuid.UUID,
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum score threshold"),
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> list[ApplicationOut]:
    """Ranked shortlist — all non-rejected candidates above min_score, sorted by final_score."""
    apps = await application_service.get_ranked_shortlist(db, job_id, min_score=min_score)
    return await _enrich_many(db, apps)


@router.get("/export", response_class=StreamingResponse)
async def export_csv(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> StreamingResponse:
    """Export all applications for a job as CSV — standard in every real ATS."""
    apps = await application_service.list_by_job(db, job_id, limit=10000)
    if not apps:
        raise HTTPException(status_code=404, detail="No applications found for this job")

    candidate_ids = list({a.candidate_id for a in apps})
    result = await db.execute(select(Candidate).where(Candidate.id.in_(candidate_ids)))
    cand_map = {c.id: c for c in result.scalars().all()}

    job = await db.get(Job, job_id)
    job_title = job.title if job else str(job_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Email", "Phone", "Stage", "Resume Score", "Test Score",
        "Interview Score", "Final Score", "Resume Quality",
        "Matched Skills", "Missing Skills", "Applied At", "Rejection Reason",
    ])
    for a in apps:
        c = cand_map.get(a.candidate_id)
        writer.writerow([
            c.full_name if c else "",
            c.email if c else "",
            c.phone if c else "",
            a.stage,
            f"{a.resume_score:.1f}" if a.resume_score is not None else "",
            f"{a.test_score:.1f}" if a.test_score is not None else "",
            f"{a.interview_score:.1f}" if a.interview_score is not None else "",
            f"{a.final_score:.1f}" if a.final_score is not None else "",
            a.resume_quality_score if a.resume_quality_score is not None else "",
            ", ".join(a.matched_skills or []),
            ", ".join(a.missing_skills or []),
            a.applied_at.strftime("%Y-%m-%d %H:%M") if a.applied_at else "",
            a.rejection_reason or "",
        ])

    output.seek(0)
    filename = f"{job_title.replace(' ', '_')}_candidates.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/by-candidate/{candidate_id}", response_model=list[ApplicationOut])
async def list_by_candidate(
    candidate_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> list[ApplicationOut]:
    result = await db.execute(
        select(Application).where(Application.candidate_id == candidate_id)
        .order_by(Application.applied_at.desc())
        .limit(limit).offset(offset)
    )
    apps = list(result.scalars().all())
    return await _enrich_many(db, apps)


@router.post("/", response_model=ApplicationOut, status_code=201)
async def create_application(
    body: CreateApplicationIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.create(
        db,
        job_id=body.job_id,
        candidate_id=body.candidate_id,
        resume_score=body.resume_score,
        matched_skills=body.matched_skills,
        missing_skills=body.missing_skills,
    )
    return await _enrich(db, app)


@router.get("/{app_id}", response_model=ApplicationOut)
async def get_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return await _enrich(db, app)


@router.patch("/{app_id}/stage", response_model=ApplicationOut)
async def advance_stage(
    app_id: uuid.UUID,
    body: StageIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app = await application_service.update_stage(
        db, app, body.stage,
        rejection_reason=body.rejection_reason,
    )
    return await _enrich(db, app)


@router.post("/webhook/test-score", response_model=ApplicationOut)
async def test_score_webhook(
    body: TestScoreIn,
    app_id: uuid.UUID = Query(..., description="Application UUID — provided by the test platform callback URL"),
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
    db: AsyncSession = Depends(get_db),
) -> ApplicationOut:
    """Public webhook — called by HackerRank/Mettl/any test platform to auto-ingest scores."""
    if not settings.WEBHOOK_SECRET or x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Webhook-Secret")
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app = await application_service.record_test_score(db, app, body.test_score)
    return await _enrich(db, app)


@router.post("/{app_id}/test-score", response_model=ApplicationOut)
async def record_test_score(
    app_id: uuid.UUID,
    body: TestScoreIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app = await application_service.record_test_score(db, app, body.test_score)
    return await _enrich(db, app)


@router.post("/{app_id}/reject", response_model=ApplicationOut)
async def reject_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    already_rejected = app.stage == "rejected"
    app = await application_service.update_stage(db, app, "rejected", status="rejected", validate=False)
    candidate: Candidate | None = await db.get(Candidate, app.candidate_id)
    job: Job | None = await db.get(Job, app.job_id)
    email_sent = False
    if candidate and job and not already_rejected:
        email_sent = await send_rejection(candidate.email, candidate.full_name, job.title)
    email_label = "sent" if email_sent else ("disabled" if not settings.SMTP_ENABLED else "already_sent" if already_rejected else "failed")
    return await _enrich(db, app, email_sent=email_sent, email_status=email_label)


@router.post("/{app_id}/offer", response_model=ApplicationOut)
async def make_offer(
    app_id: uuid.UUID,
    body: SendOfferIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    already_offered = app.stage == "offered"
    app = await application_service.update_stage(db, app, "offered", status="offered", validate=False)
    candidate: Candidate | None = await db.get(Candidate, app.candidate_id)
    job: Job | None = await db.get(Job, app.job_id)
    email_sent = False
    if candidate and job and not already_offered:
        email_sent = await send_offer(candidate.email, candidate.full_name, job.title, body.draft)
    email_label = "sent" if email_sent else ("disabled" if not settings.SMTP_ENABLED else "already_sent" if already_offered else "failed")
    return await _enrich(db, app, email_sent=email_sent, email_status=email_label)


@router.post("/{app_id}/send-test-link", response_model=ApplicationOut)
async def send_test_link_route(
    app_id: uuid.UUID,
    body: SendTestLinkIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    already_sent = app.stage in ("testing", "test_sent")
    candidate: Candidate | None = await db.get(Candidate, app.candidate_id)
    job: Job | None = await db.get(Job, app.job_id)
    email_sent = False
    if candidate and job and not already_sent:
        email_sent = await send_test_link(
            candidate_email=candidate.email,
            candidate_name=candidate.full_name,
            job_title=job.title,
            test_link=body.test_link,
            deadline=body.deadline,
        )
    app = await application_service.update_stage(db, app, "testing", validate=False)
    email_label = "sent" if email_sent else ("disabled" if not settings.SMTP_ENABLED else "already_sent" if already_sent else "failed")
    return await _enrich(db, app, email_sent=email_sent, email_status=email_label)


@router.delete("/{app_id}", status_code=204)
async def delete_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> Response:
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await application_service.delete(db, app)
    return Response(status_code=204)


@router.patch("/{app_id}/weights", response_model=ApplicationOut)
async def update_weights(
    app_id: uuid.UUID,
    body: WeightsIn,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> ApplicationOut:
    """HR configures resume vs test score weighting per application."""
    if body.resume_weight + body.test_weight != 100:
        raise HTTPException(status_code=400, detail="resume_weight + test_weight must equal 100")
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.resume_weight = body.resume_weight
    app.test_weight = body.test_weight
    app.final_score = application_service._compute_final(app)
    await db.commit()
    await db.refresh(app)
    return await _enrich(db, app)


@router.get("/{app_id}/offer-draft", response_model=OfferDraftOut)
async def get_offer_draft(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> OfferDraftOut:
    """Generate a Gemini-drafted personalised offer email for HR to review."""
    app = await application_service.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    candidate: Candidate | None = await db.get(Candidate, app.candidate_id)
    job: Job | None = await db.get(Job, app.job_id)
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")
    draft = await draft_offer_email(
        candidate_name=candidate.full_name,
        job_title=job.title,
        matched_skills=app.matched_skills or [],
        final_score=app.final_score or 0,
    )
    return OfferDraftOut(draft=draft, candidate_name=candidate.full_name, job_title=job.title)
