"""
In-memory hiring pipeline workflow service.
Manages candidate state transitions and triggers email notifications.
Intended as a lightweight layer on top of the DB-backed services for
pipeline orchestration until a dedicated workflow table is added.
"""
from __future__ import annotations

import secrets
import logging
from datetime import datetime

from services.email_service import (
    send_test_invite,
    send_tech_interview_invite,
    send_hr_interview_invite,
    send_offer_letter,
    send_rejection,
)

log = logging.getLogger(__name__)

STAGES = [
    "applied", "shortlisted", "testing", "interviewing", "offered", "rejected",
]

STAGE_LABELS = {
    "applied": "Applied",
    "shortlisted": "Shortlisted",
    "testing": "Testing",
    "interviewing": "Interviewing",
    "offered": "Offered",
    "rejected": "Rejected",
}

_candidates: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

def _compute_final_score(candidate: dict) -> float:
    weights = {"fit": 0.40, "test": 0.20, "tech": 0.25, "hr": 0.15}
    score = total_w = 0.0
    for key, w in [
        ("fit_score", weights["fit"]),
        ("test_score", weights["test"]),
        ("tech_interview_score", weights["tech"]),
        ("hr_interview_score", weights["hr"]),
    ]:
        if candidate.get(key) is not None:
            score += candidate[key] * w
            total_w += w
    return round(score / total_w, 1) if total_w > 0 else 0.0


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_candidate(data: dict) -> dict:
    cid = data.get("id") or secrets.token_hex(8)
    candidate = {
        "id": cid,
        "full_name": data.get("full_name", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "job_title": data.get("job_title", ""),
        "job_id": data.get("job_id", ""),
        "source": data.get("source", "manual"),
        "stage": "applied",
        "fit_score": data.get("fit_score"),
        "skills": data.get("skills", []),
        "experience_years": data.get("experience_years"),
        "test_score": None, "test_link": None, "test_token": None, "test_submitted_at": None,
        "tech_interview_score": None, "tech_interview_feedback": None,
        "tech_interviewer_email": None, "tech_interview_scheduled_at": None,
        "hr_interview_score": None, "hr_interview_feedback": None, "hr_interview_scheduled_at": None,
        "final_score": data.get("fit_score"),
        "created_at": datetime.utcnow().isoformat(),
    }
    _candidates[cid] = candidate
    return candidate


def get_candidate(candidate_id: str) -> dict | None:
    return _candidates.get(candidate_id)


def get_all_candidates(job_id: str | None = None, stage: str | None = None) -> list[dict]:
    candidates = list(_candidates.values())
    if job_id:
        candidates = [c for c in candidates if c.get("job_id") == job_id]
    if stage:
        candidates = [c for c in candidates if c.get("stage") == stage]
    return sorted(candidates, key=lambda c: c.get("final_score") or 0, reverse=True)


def update_candidate(candidate_id: str, updates: dict) -> dict | None:
    if candidate_id not in _candidates:
        return None
    _candidates[candidate_id].update(updates)
    _candidates[candidate_id]["final_score"] = _compute_final_score(_candidates[candidate_id])
    return _candidates[candidate_id]


def bulk_import_candidates(candidates: list[dict]) -> list[dict]:
    created = []
    for c in candidates:
        existing = next((x for x in _candidates.values() if x["email"] == c.get("email", "")), None)
        if existing:
            update_candidate(existing["id"], {
                "fit_score": c.get("fit_score"),
                "skills": c.get("skills", []),
                "experience_years": c.get("experience_years"),
                "final_score": c.get("fit_score"),
                "stage": "shortlisted" if (c.get("fit_score") or 0) >= 60 else "applied",
            })
            created.append(existing)
        else:
            created.append(create_candidate(c))
    return created


# ---------------------------------------------------------------------------
# Workflow actions
# ---------------------------------------------------------------------------

def send_test(candidate_id: str, test_platform_url: str, job_title: str) -> dict:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found")
    token = secrets.token_urlsafe(32)
    test_link = f"{test_platform_url}?token={token}&candidate={candidate_id}"
    email_sent = send_test_invite(
        to=candidate["email"], candidate_name=candidate["full_name"],
        job_title=job_title, test_link=test_link,
    )
    return update_candidate(candidate_id, {
        "stage": "test_sent", "test_token": token,
        "test_link": test_link, "email_sent": email_sent,
    })


def ingest_test_score(token: str, score: float) -> dict:
    candidate = next((c for c in _candidates.values() if c.get("test_token") == token), None)
    if not candidate:
        raise ValueError(f"No candidate found for token {token}")
    return update_candidate(candidate["id"], {
        "test_score": score, "stage": "test_completed",
        "test_submitted_at": datetime.utcnow().isoformat(),
    })


def schedule_tech_interview(candidate_id: str, scheduled_at: str, interviewer_email: str, interviewer_name: str, job_title: str, meet_link: str = "") -> dict:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found")
    email_sent = send_tech_interview_invite(
        to=candidate["email"], candidate_name=candidate["full_name"],
        job_title=job_title, scheduled_at=scheduled_at,
        interviewer_name=interviewer_name, meet_link=meet_link,
    )
    return update_candidate(candidate_id, {
        "stage": "tech_interview_scheduled",
        "tech_interviewer_email": interviewer_email,
        "tech_interview_scheduled_at": scheduled_at,
        "email_sent": email_sent,
    })


def submit_tech_feedback(candidate_id: str, score: float, feedback: str) -> dict:
    if not get_candidate(candidate_id):
        raise ValueError(f"Candidate {candidate_id} not found")
    return update_candidate(candidate_id, {
        "stage": "tech_interview_completed",
        "tech_interview_score": score,
        "tech_interview_feedback": feedback,
    })


def schedule_hr_interview(candidate_id: str, scheduled_at: str, job_title: str, meet_link: str = "") -> dict:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found")
    email_sent = send_hr_interview_invite(
        to=candidate["email"], candidate_name=candidate["full_name"],
        job_title=job_title, scheduled_at=scheduled_at, meet_link=meet_link,
    )
    return update_candidate(candidate_id, {
        "stage": "hr_interview_scheduled",
        "hr_interview_scheduled_at": scheduled_at,
        "email_sent": email_sent,
    })


def submit_hr_feedback(candidate_id: str, score: float, feedback: str) -> dict:
    if not get_candidate(candidate_id):
        raise ValueError(f"Candidate {candidate_id} not found")
    return update_candidate(candidate_id, {
        "stage": "hr_interview_completed",
        "hr_interview_score": score,
        "hr_interview_feedback": feedback,
    })


def send_offer(candidate_id: str, job_title: str, company_name: str = "FairHire AI", joining_date: str = "To be confirmed", ctc: str = "As discussed") -> dict:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found")
    email_sent = send_offer_letter(
        to=candidate["email"], candidate_name=candidate["full_name"],
        job_title=job_title, company_name=company_name,
        joining_date=joining_date, ctc=ctc,
    )
    return update_candidate(candidate_id, {
        "stage": "offer_sent",
        "offer_sent_at": datetime.utcnow().isoformat(),
        "email_sent": email_sent,
    })


def reject_candidate(candidate_id: str, job_title: str) -> dict:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found")
    send_rejection(
        to=candidate["email"], candidate_name=candidate["full_name"], job_title=job_title,
    )
    return update_candidate(candidate_id, {"stage": "rejected"})


def get_pipeline_stats(job_id: str | None = None) -> dict:
    candidates = get_all_candidates(job_id=job_id)
    stage_counts: dict[str, int] = {s: 0 for s in STAGES}
    for c in candidates:
        stage = c.get("stage", "applied")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    scores = [c["final_score"] for c in candidates if c.get("final_score") is not None]
    return {
        "total": len(candidates),
        "stage_breakdown": stage_counts,
        "avg_final_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "top_score": max(scores) if scores else 0,
        "hired": stage_counts.get("hired", 0),
        "rejected": stage_counts.get("rejected", 0),
        "in_progress": len([c for c in candidates if c.get("stage") not in ("hired", "rejected")]),
    }
