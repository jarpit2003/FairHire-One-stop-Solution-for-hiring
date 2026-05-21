import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, field_validator

from db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Pydantic mixin — reusable max-length validators for free-text inputs
# ---------------------------------------------------------------------------

class TextLengthMixin(BaseModel):
    @field_validator("description", "notes", "feedback", "resume_text", mode="before", check_fields=False)
    @classmethod
    def _cap_text(cls, v: str | None) -> str | None:
        if v and len(v) > 20_000:
            raise ValueError("Field exceeds 20,000 character limit")
        return v


class HRUser(Base):
    __tablename__ = "hr_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="hr")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(1000))
    resume_text: Mapped[str | None] = mapped_column(Text)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    form_url: Mapped[str | None] = mapped_column(String(1000))
    published_platforms: Mapped[list | None] = mapped_column(JSON, default=list)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)

    resume_score: Mapped[float | None] = mapped_column(Float)
    test_score: Mapped[float | None] = mapped_column(Float)
    interview_score: Mapped[float | None] = mapped_column(Float)
    hr_interview_score: Mapped[float | None] = mapped_column(Float)
    final_score: Mapped[float | None] = mapped_column(Float)

    # Score component breakdown — stored so UI can show per-dimension bars
    score_impact: Mapped[float | None] = mapped_column(Float)
    score_semantic: Mapped[float | None] = mapped_column(Float)
    score_skill: Mapped[float | None] = mapped_column(Float)
    score_cert: Mapped[float | None] = mapped_column(Float)
    score_experience: Mapped[float | None] = mapped_column(Float)

    # Resume quality (0-100) stored from upload
    resume_quality_score: Mapped[int | None] = mapped_column(Integer)

    resume_weight: Mapped[int] = mapped_column(Integer, default=60)
    test_weight: Mapped[int] = mapped_column(Integer, default=40)

    stage: Mapped[str] = mapped_column(
        String(50), default="applied"
    )  # applied | shortlisted | testing | interviewing | offered | rejected
    status: Mapped[str] = mapped_column(String(50), default="active")

    rejection_reason: Mapped[str | None] = mapped_column(String(500))

    matched_skills: Mapped[list | None] = mapped_column(JSON)
    missing_skills: Mapped[list | None] = mapped_column(JSON)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    interviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meet_link: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)


class FormSubmission(Base):
    """
    Raw record of every public form / intake submission.
    Stored independently so the original applicant data is never lost
    even if candidate deduplication merges or updates the Candidate row.
    """
    __tablename__ = "form_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)

    # Raw fields exactly as submitted
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(1000))
    resume_text: Mapped[str | None] = mapped_column(Text)
    cover_note: Mapped[str | None] = mapped_column(Text)

    # Processing outcome
    resume_score: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50), default="web_form")  # web_form | api | google_form
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
