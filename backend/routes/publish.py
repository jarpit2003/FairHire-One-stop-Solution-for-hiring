"""
routes/publish.py

POST /api/v1/jobs/{job_id}/publish
  - Accepts a list of platforms to publish to
  - Returns per-platform result (success, url, message)
  - Stores published_platforms on the Job record
"""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Job, HRUser
from services.auth_service import get_current_user
from services.publisher_service import (
    publish_linkedin,
    publish_naukri,
    publish_x,
    create_google_form,
    PublishResult,
)

router = APIRouter()


class PublishRequest(BaseModel):
    platforms: list[str]   # e.g. ["linkedin", "naukri", "x", "google_form"]


class PlatformResult(BaseModel):
    platform: str
    success: bool
    url: str | None
    message: str


class PublishResponse(BaseModel):
    job_id: str
    results: list[PlatformResult]
    published_platforms: list[str]


@router.post("/{job_id}/publish", response_model=PublishResponse)
async def publish_job(
    job_id: uuid.UUID,
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
    _: HRUser = Depends(get_current_user),
) -> PublishResponse:
    job: Job | None = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    title       = job.title
    description = job.description or ""
    form_url    = job.form_url

    results: list[PublishResult] = []

    for platform in body.platforms:
        if platform == "linkedin":
            results.append(publish_linkedin(title, description, form_url))

        elif platform == "naukri":
            results.append(publish_naukri(title, description, form_url))

        elif platform == "x":
            results.append(await publish_x(title, description, form_url))

        elif platform == "google_form":
            result = await create_google_form(str(job_id), title, description)
            # If form created successfully, store URL on job
            if result.success and result.url:
                job.form_url = result.url
                await db.commit()
                await db.refresh(job)
            results.append(result)

        else:
            results.append(PublishResult(
                platform=platform, success=False, url=None,
                message=f"Unknown platform: {platform}",
            ))

    # Update published_platforms on job
    existing = list(job.published_platforms or [])
    for r in results:
        if r.success and r.platform not in existing:
            existing.append(r.platform)
    job.published_platforms = existing
    await db.commit()

    return PublishResponse(
        job_id=str(job_id),
        results=[PlatformResult(**r.__dict__) for r in results],
        published_platforms=existing,
    )
