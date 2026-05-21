"""
services/application_service.py

CRUD + scoring logic for the Application pipeline entity.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from db.models import Application

# ---------------------------------------------------------------------------
# Valid pipeline stages and allowed forward transitions
# Real ATS systems enforce stage order — you can't move from Applied to Offered
# without going through Shortlisted → Testing → Interviewing first.
# Backward moves (e.g. re-opening a rejected candidate) are allowed explicitly.
# ---------------------------------------------------------------------------

VALID_STAGES = {
    "applied", "shortlisted", "testing", "interviewing", "offered", "rejected",
}

# Each stage can only move to these next stages
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "applied":      {"shortlisted", "rejected"},
    "shortlisted":  {"testing", "interviewing", "rejected"},
    "testing":      {"interviewing", "shortlisted", "rejected"},
    "interviewing": {"offered", "rejected"},
    "offered":      {"rejected"},          # offer can be rescinded
    "rejected":     {"applied"},           # re-open a rejected candidate
}

_STAGE_ORDER = ["applied", "shortlisted", "testing", "interviewing", "offered", "rejected"]


def validate_stage_transition(current: str, target: str) -> None:
    """Raise HTTPException if the stage transition is not allowed."""
    if target not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage '{target}'. Valid: {sorted(VALID_STAGES)}")
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move from '{current}' to '{target}'. Allowed next stages: {sorted(allowed)}",
        )


async def _find_existing(
    db: AsyncSession,
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
) -> Application | None:
    """Find existing application for (candidate, job) pair."""
    result = await db.execute(
        select(Application).where(
            Application.job_id == job_id,
            Application.candidate_id == candidate_id,
        ).limit(1)
    )
    return result.scalars().first()


async def create(
    db: AsyncSession,
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    resume_score: float | None = None,
    matched_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
    score_components: dict | None = None,
    resume_quality_score: int | None = None,
) -> Application:
    """
    Upsert — if application already exists for this (candidate, job),
    update scores + skills only.
    Stage and status are NEVER touched so a candidate already in
    Shortlisted / Testing / Interviewing stays exactly where they are.
    score_components: dict with keys impact, semantic, skill, cert, experience
    """
    existing = await _find_existing(db, job_id, candidate_id)
    if existing:
        existing.resume_score = resume_score
        existing.matched_skills = matched_skills or []
        existing.missing_skills = missing_skills or []
        existing.final_score = _compute_final(existing)
        existing.updated_at = datetime.now(timezone.utc)
        if score_components:
            existing.score_impact = score_components.get("impact")
            existing.score_semantic = score_components.get("semantic")
            existing.score_skill = score_components.get("skill")
            existing.score_cert = score_components.get("cert")
            existing.score_experience = score_components.get("experience")
        if resume_quality_score is not None:
            existing.resume_quality_score = resume_quality_score
        await db.commit()
        await db.refresh(existing)
        return existing

    app = Application(
        job_id=job_id,
        candidate_id=candidate_id,
        resume_score=resume_score,
        final_score=resume_score,
        matched_skills=matched_skills or [],
        missing_skills=missing_skills or [],
        score_impact=score_components.get("impact") if score_components else None,
        score_semantic=score_components.get("semantic") if score_components else None,
        score_skill=score_components.get("skill") if score_components else None,
        score_cert=score_components.get("cert") if score_components else None,
        score_experience=score_components.get("experience") if score_components else None,
        resume_quality_score=resume_quality_score,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def delete(db: AsyncSession, app: Application) -> None:
    await db.delete(app)
    await db.commit()


async def get_by_id(db: AsyncSession, app_id: uuid.UUID) -> Application | None:
    return await db.get(Application, app_id)


async def list_by_job(
    db: AsyncSession,
    job_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
    stage: str | None = None,
) -> list[Application]:
    q = select(Application).where(Application.job_id == job_id)
    if stage:
        q = q.where(Application.stage == stage)
    q = q.order_by(Application.final_score.desc().nullslast()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_ranked_shortlist(
    db: AsyncSession,
    job_id: uuid.UUID,
    min_score: float = 0.0,
    exclude_rejected: bool = True,
) -> list[Application]:
    """
    Returns all applications for a job ranked by final_score descending.
    Used by the shortlist recommendation and chatbot ranking features.
    Real ATS systems (Greenhouse, Lever) expose this as a dedicated endpoint.
    """
    q = select(Application).where(Application.job_id == job_id)
    if exclude_rejected:
        q = q.where(Application.stage != "rejected")
    if min_score > 0:
        q = q.where(Application.final_score >= min_score)
    q = q.order_by(Application.final_score.desc().nullslast())
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_stage(
    db: AsyncSession,
    app: Application,
    stage: str,
    status: str | None = None,
    validate: bool = True,
    rejection_reason: str | None = None,
) -> Application:
    if validate:
        validate_stage_transition(app.stage, stage)
    app.stage = stage
    if status:
        app.status = status
    if rejection_reason:
        app.rejection_reason = rejection_reason
    app.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(app)
    return app


async def shortlist(db: AsyncSession, app: Application) -> Application:
    """Convenience wrapper — moves applied → shortlisted with validation."""
    return await update_stage(db, app, "shortlisted")


async def record_test_score(
    db: AsyncSession,
    app: Application,
    test_score: float,
) -> Application:
    app.test_score = test_score
    # Only advance to "testing", never regress a candidate already further along
    current_idx = _STAGE_ORDER.index(app.stage) if app.stage in _STAGE_ORDER else 0
    if current_idx < _STAGE_ORDER.index("testing"):
        app.stage = "testing"
    app.final_score = _compute_final(app)
    app.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(app)
    return app


async def record_interview_score(
    db: AsyncSession,
    app: Application,
    score: float,
    round_number: int,
) -> Application:
    if round_number == 1:
        app.interview_score = score
    else:
        app.hr_interview_score = score
    target_stage = "interviewing"
    current_idx = _STAGE_ORDER.index(app.stage) if app.stage in _STAGE_ORDER else 0
    target_idx = _STAGE_ORDER.index(target_stage)
    if target_idx > current_idx:
        app.stage = target_stage
    app.final_score = _compute_final(app)
    app.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(app)
    return app


def _compute_final(app: Application) -> float:
    """
    Weighted composite score.
    Weights are stored on the application so HR can configure per-job.
    Only includes components that have been scored.
    """
    scores: list[tuple[float, float]] = []

    if app.resume_score is not None:
        scores.append((app.resume_score, app.resume_weight))
    if app.test_score is not None:
        scores.append((app.test_score, app.test_weight))
    if app.interview_score is not None:
        scores.append((app.interview_score, app.test_weight))
    if app.hr_interview_score is not None:
        scores.append((app.hr_interview_score, app.resume_weight // 2))

    if not scores:
        return 0.0

    total_weight = sum(w for _, w in scores)
    return round(sum(s * w for s, w in scores) / total_weight, 1)
