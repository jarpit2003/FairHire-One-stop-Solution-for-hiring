"""
services/offer_service.py

Generates a personalised offer email draft using rule-based templates.
HR reviews and edits before sending — never auto-sends without approval.
Personalisation is based on matched skills and score tier.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


async def draft_offer_email(
    candidate_name: str,
    job_title: str,
    matched_skills: list[str],
    final_score: float,
) -> str:
    """Returns a personalised offer email body based on matched skills and score."""
    top_skills = matched_skills[:3] if matched_skills else []

    skill_sentence = (
        f"Your expertise in {', '.join(top_skills[:-1])} and {top_skills[-1]}"
        if len(top_skills) >= 2
        else f"Your expertise in {top_skills[0]}" if top_skills
        else "Your strong technical background"
    )

    score_comment = (
        "Your profile stood out as one of our strongest candidates."
        if final_score >= 80
        else "Your profile was a strong match for what we are looking for."
        if final_score >= 65
        else "After careful evaluation, we believe you are a great fit for this role."
    )

    return f"""Dear {candidate_name},

Congratulations! We are delighted to offer you the position of {job_title}.

{score_comment} {skill_sentence} aligns perfectly with the requirements of this role.

Our HR team will be in touch shortly with the formal offer letter, compensation details, and onboarding information. Please confirm your acceptance within 3 business days.

We look forward to welcoming you to the team!

Best regards,
FairHire AI Recruitment Team"""
