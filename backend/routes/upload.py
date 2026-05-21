from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel
import asyncio
from functools import partial

from config import settings
from services.parser import parse_resume
from services.profile_extractor import CandidateProfile, extract_profile, contact_confidence
from services.link_verifier import verify_links, LinkResult
from services.resume_quality import compute_resume_quality

router = APIRouter()

_ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ProfileSummary(BaseModel):
    skills: list[str]
    education: list[str]
    certifications: list[str]
    experience_years: int | None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None


class VerifiedLink(BaseModel):
    url: str
    reachable: bool
    platform: str
    detail: str
    commit_activity: bool


class UploadResponse(BaseModel):
    filename: str
    size_bytes: int
    detected_type: str
    full_text: str = ""
    extracted_text_preview: str
    profile_summary: ProfileSummary | None = None
    verified_links: list[VerifiedLink] = []
    used_fallback_parser: bool = False
    resume_quality: dict = {}
    contact_confidence: int = 0
    message: str


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/resume",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, parse and profile a candidate resume",
    description=(
        "Accepts PDF or DOCX resume files up to the configured size limit. "
        "Returns structured profile and verified links. "
        "Uses pypdf as primary parser with pdfplumber fallback for complex layouts."
    ),
)
async def upload_resume(file: UploadFile) -> UploadResponse:
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: PDF, DOC, DOCX.",
        )

    contents = await file.read()

    if len(contents) / (1024 * 1024) > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    loop = asyncio.get_event_loop()
    parsed = await loop.run_in_executor(
        None,
        partial(parse_resume, contents=contents, filename=file.filename or "unknown", content_type=file.content_type or ""),
    )

    profile: CandidateProfile | None = None
    links: list[LinkResult] = []

    if parsed.full_text:
        profile = extract_profile(parsed.full_text, parsed.raw_text_for_contacts)
        links   = await verify_links(parsed.full_text)

    ps = _to_profile_summary(profile)
    conf = contact_confidence(
        ps.email if ps else None,
        ps.phone if ps else None,
        ps.full_name if ps else None,
    ) if ps else 0

    return UploadResponse(
        filename=parsed.filename,
        size_bytes=parsed.size_bytes,
        detected_type=parsed.detected_type,
        full_text=parsed.full_text,
        extracted_text_preview=parsed.extracted_text_preview,
        profile_summary=ps,
        verified_links=[_to_verified_link(l) for l in links],
        used_fallback_parser=parsed.used_fallback_parser,
        resume_quality=compute_resume_quality(parsed.full_text) if parsed.full_text else {},
        contact_confidence=conf,
        message="Resume parsed and profiled successfully.",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_profile_summary(profile: CandidateProfile | None) -> ProfileSummary | None:
    if profile is None:
        return None
    return ProfileSummary(
        skills=list(profile.skills),
        education=list(profile.education),
        certifications=list(profile.certifications),
        experience_years=profile.experience_years,
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
    )


def _to_verified_link(link: LinkResult) -> VerifiedLink:
    return VerifiedLink(
        url=link.url,
        reachable=link.reachable,
        platform=link.platform,
        detail=link.detail,
        commit_activity=link.commit_activity,
    )
