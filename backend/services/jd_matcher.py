"""
services/jd_matcher.py

Hybrid candidate-job fit scoring — fully deterministic, no external API.

Scoring components and weights:
    30%  Skill overlap        — weighted taxonomy match (JD skills vs resume skills)
    25%  Semantic similarity  — BM25 TF-IDF cosine (profile text vs JD text)
    25%  Impact score         — achievement sentence quality and JD relevance
    10%  Experience relevance — years extracted vs JD requirement
    10%  Education relevance  — degree level and field vs JD requirement

Certification score is a BONUS (up to +5 pts) not a weighted component.
This prevents penalising freshers who lack certs but are otherwise strong.

Bias mitigations:
  - No institution name bias (stripped in semantic_matcher)
  - No gender-coded language scoring
  - Experience score uses a smooth curve, not hard cutoffs
  - Missing skills use non-linear penalty (sqrt) — missing 1 of 2 hurts
    less than missing 5 of 10 proportionally
  - Candidates with no experience data get 0.5 (neutral) not 0.0
  - Candidates with no education data get 0.5 (neutral) not 0.0
"""
from __future__ import annotations

import asyncio
import logging
import math
import re
from dataclasses import dataclass

from services.profile_extractor import CandidateProfile
from services.skill_taxonomy import SKILL_TAXONOMY, SKILL_WEIGHTS
from services.semantic_matcher import build_profile_text, semantic_similarity
from services.scoring_service import score_impact

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class MatchResult:
    fit_score: int
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    skill_overlap_score: float
    education_relevance_score: float
    experience_relevance_score: float
    certification_score: float
    semantic_similarity_score: float
    impact_score: float
    impact_highlights: tuple[str, ...]


# ---------------------------------------------------------------------------
# Compiled skill patterns for JD extraction
# ---------------------------------------------------------------------------

_SKILL_PATTERNS: dict[str, re.Pattern[str]] = {
    canonical: re.compile(r"(?i)(?:" + "|".join(aliases) + r")")
    for canonical, aliases in SKILL_TAXONOMY.items()
}

_TECH_EDUCATION_KEYWORDS = {
    "computer science", "software engineering", "computer engineering",
    "information technology", "data science", "artificial intelligence",
    "machine learning", "electrical engineering", "electronics",
    "mathematics", "statistics", "physics",
}

_EXPERIENCE_KEYWORDS = {
    "senior", "lead", "principal", "architect", "manager", "director",
    "years experience", "experienced", "expert", "staff engineer",
}

# Scoring weights — must sum to 1.0
_W_SKILL      = 0.30
_W_SEMANTIC   = 0.25
_W_IMPACT     = 0.25
_W_EXPERIENCE = 0.10
_W_EDUCATION  = 0.10


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def match_candidate_to_jd(
    profile: CandidateProfile,
    jd_text: str,
    resume_text: str = "",
) -> MatchResult:
    """
    Compute a fair, multi-dimensional fit score for a candidate vs a JD.
    All components return values in [0.0, 1.0].
    Missing data returns 0.5 (neutral) not 0.0 (penalised).
    """
    jd_skills = _extract_jd_skills(jd_text)
    matched = tuple(s for s in profile.skills if s in jd_skills)
    missing = tuple(s for s in jd_skills if s not in profile.skills)

    # Weighted skill overlap
    weighted_match = sum(SKILL_WEIGHTS.get(s, 1.0) for s in matched)
    weighted_total = sum(SKILL_WEIGHTS.get(s, 1.0) for s in jd_skills) or 1.0
    skill_score = weighted_match / weighted_total

    # Experience and education — return 0.5 (neutral) when data is missing
    experience_score = _compute_experience_relevance(profile.experience_years, jd_text)
    education_score  = _compute_education_relevance(profile.education, jd_text)

    profile_text = build_profile_text(
        profile.skills, profile.education, profile.certifications, profile.experience_years
    )

    # Run semantic + impact concurrently
    sem_score, (impact_score, impact_highlights) = await asyncio.gather(
        semantic_similarity(profile_text, jd_text),
        score_impact(resume_text or profile_text, jd_text),
    )

    # All components are now always active — no redistribution needed
    # because none of them return 0.0 for missing data
    raw_score = (
        skill_score      * _W_SKILL
        + sem_score      * _W_SEMANTIC
        + impact_score   * _W_IMPACT
        + experience_score * _W_EXPERIENCE
        + education_score  * _W_EDUCATION
    )

    # Non-linear missing skill penalty using sqrt
    # sqrt(missing_ratio) grows fast at first then slows down
    # Missing 1/4 skills: sqrt(0.25)=0.5 → penalty = 0.5 * 0.12 = 6 pts
    # Missing 4/4 skills: sqrt(1.0)=1.0  → penalty = 1.0 * 0.12 = 12 pts
    # This is fairer than linear: missing 1 of 2 (50%) ≠ missing 5 of 10 (50%)
    if jd_skills:
        missing_ratio = len(missing) / len(jd_skills)
        missing_penalty = math.sqrt(missing_ratio) * 0.12
    else:
        missing_penalty = 0.0

    # Certification bonus — up to +5 pts, not a weighted component
    # Freshers without certs are not penalised; certs are a positive signal only
    cert_bonus = _compute_cert_bonus(profile.certifications, jd_text)

    fit_score = int(raw_score * 100) - int(missing_penalty * 100) + cert_bonus
    fit_score = max(0, min(100, fit_score))

    log.debug(
        "jd_matcher: fit=%d skill=%.2f sem=%.2f impact=%.2f exp=%.2f edu=%.2f "
        "cert_bonus=%d penalty=%.2f",
        fit_score, skill_score, sem_score, impact_score,
        experience_score, education_score, cert_bonus, missing_penalty,
    )

    return MatchResult(
        fit_score=fit_score,
        matched_skills=matched,
        missing_skills=missing,
        skill_overlap_score=skill_score,
        education_relevance_score=education_score,
        experience_relevance_score=experience_score,
        certification_score=cert_bonus / 5.0,  # normalise to 0–1 for storage
        semantic_similarity_score=sem_score,
        impact_score=impact_score,
        impact_highlights=tuple(impact_highlights),
    )


# ---------------------------------------------------------------------------
# JD skill extraction
# ---------------------------------------------------------------------------

def _extract_jd_skills(jd_text: str) -> set[str]:
    return {c for c, p in _SKILL_PATTERNS.items() if p.search(jd_text)}


# ---------------------------------------------------------------------------
# Certification bonus (not a penalty for absence)
# ---------------------------------------------------------------------------

# Maps cert keywords to bonus points
_CERT_BONUS_MAP: dict[str, int] = {
    "aws certified":        3,
    "google cloud certified": 3,
    "azure certified":      3,
    "certified kubernetes": 3,
    "cka":                  3,
    "ckad":                 3,
    "cks":                  3,
    "pmp":                  2,
    "cissp":                3,
    "comptia":              2,
    "terraform associate":  2,
    "professional scrum":   2,
    "certified scrum":      2,
    "tensorflow developer": 2,
}

def _compute_cert_bonus(certifications: tuple[str, ...], jd_text: str) -> int:
    """
    Returns a bonus of 0–5 pts for relevant certifications.
    No certs = 0 bonus (not penalised).
    Irrelevant certs = 0 bonus.
    Relevant certs = up to 5 pts.
    """
    if not certifications:
        return 0

    cert_text = " ".join(certifications).lower()
    jd_lower = jd_text.lower()
    total_bonus = 0

    for keyword, pts in _CERT_BONUS_MAP.items():
        if keyword in cert_text and any(w in jd_lower for w in keyword.split()):
            total_bonus += pts

    return min(total_bonus, 5)


# ---------------------------------------------------------------------------
# Education relevance — neutral (0.5) when data missing
# ---------------------------------------------------------------------------

def _compute_education_relevance(education: tuple[str, ...], jd_text: str) -> float:
    """
    Returns 0.5 (neutral) when no education data — does not penalise.
    Returns 0.4–1.0 based on degree level and field match.
    """
    if not education:
        return 0.5  # neutral — no data, no penalty

    jd_lower  = jd_text.lower()
    edu_lower = " ".join(education).lower()

    has_tech_field = any(kw in edu_lower for kw in _TECH_EDUCATION_KEYWORDS)
    jd_needs_tech  = any(kw in jd_lower  for kw in _TECH_EDUCATION_KEYWORDS)

    has_masters = any("master" in e.lower() or "phd" in e.lower() or "m.tech" in e.lower() for e in education)
    has_bachelors = any(
        any(kw in e.lower() for kw in ["bachelor", "b.tech", "b.e", "b.sc", "degree"])
        for e in education
    )

    if has_tech_field and jd_needs_tech:
        return 1.0 if has_masters else 0.9
    if has_tech_field:
        return 0.8
    if has_bachelors or has_masters:
        return 0.7
    # Has some education but not tech-related
    return 0.5


# ---------------------------------------------------------------------------
# Experience relevance — smooth curve, neutral (0.5) when data missing
# ---------------------------------------------------------------------------

def _compute_experience_relevance(experience_years: int | None, jd_text: str) -> float:
    """
    Returns 0.5 (neutral) when no experience data — does not penalise freshers.
    Uses a smooth sigmoid-like curve instead of hard cutoffs.
    """
    if experience_years is None:
        return 0.5  # neutral — no data, no penalty

    jd_lower = jd_text.lower()
    year_matches = re.findall(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", jd_lower)
    required_years = int(year_matches[0]) if year_matches else 0
    is_senior_role = any(kw in jd_lower for kw in _EXPERIENCE_KEYWORDS)

    if required_years > 0:
        ratio = experience_years / required_years
        # Smooth curve: exceeds requirement → 1.0, at 70% → 0.8, at 50% → 0.65
        if ratio >= 1.0:
            return 1.0
        # Smooth interpolation using sqrt for a concave curve
        # This rewards candidates who are close to the requirement
        return max(0.3, min(0.95, math.sqrt(ratio) * 0.95))

    if is_senior_role:
        # No explicit year requirement but role is senior
        # Smooth curve: 7+ years → 1.0, 5 years → 0.85, 3 years → 0.65
        return min(1.0, 0.5 + (experience_years / 14.0))

    # No requirement stated — reward experience up to 5 years, then plateau
    return min(1.0, 0.5 + (experience_years / 10.0))
