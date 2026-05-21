"""
Recruiter analytics service for dashboard summary.
Processes ranked shortlist results and computes key metrics.
"""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from services.jd_matcher import MatchResult


@dataclass(frozen=True, slots=True)
class CandidateMatchSummary:
    candidate_id: str
    fit_score: int
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True, slots=True)
class AnalyticsSummary:
    total_candidates: int
    average_fit_score: float
    top_candidate_score: int
    shortlisted_count: int
    recommended_for_interview_count: int
    common_missing_skills: tuple[str, ...]
    score_distribution: dict[str, int]
    recommendation_breakdown: dict[str, int]


def compute_analytics_summary(candidates: list[CandidateMatchSummary]) -> AnalyticsSummary:
    if not candidates:
        return _empty_summary()

    fit_scores = [c.fit_score for c in candidates]
    recommendation_counts = Counter(c.recommendation for c in candidates)

    all_missing: list[str] = []
    for c in candidates:
        all_missing.extend(c.missing_skills)

    common_missing_skills = tuple(
        f"{skill} ({count})"
        for skill, count in Counter(all_missing).most_common(5)
    )

    return AnalyticsSummary(
        total_candidates=len(candidates),
        average_fit_score=round(sum(fit_scores) / len(fit_scores), 1),
        top_candidate_score=max(fit_scores),
        shortlisted_count=recommendation_counts.get("Shortlisted", 0),
        recommended_for_interview_count=sum(1 for c in candidates if c.fit_score >= 70),
        common_missing_skills=common_missing_skills,
        score_distribution=_compute_score_distribution(fit_scores),
        recommendation_breakdown=dict(recommendation_counts),
    )


def create_candidate_summary(candidate_id: str, match_result: MatchResult) -> CandidateMatchSummary:
    return CandidateMatchSummary(
        candidate_id=candidate_id,
        fit_score=match_result.fit_score,
        matched_skills=match_result.matched_skills,
        missing_skills=match_result.missing_skills,
        recommendation=_determine_recommendation(match_result.fit_score),
    )


def generate_ai_insights(summary: AnalyticsSummary) -> dict[str, str]:
    if summary.average_fit_score >= 70:
        pool_quality = "Strong candidate pool with good alignment."
    elif summary.average_fit_score >= 50:
        pool_quality = "Moderate pool — some candidates fit well."
    else:
        pool_quality = "Low alignment — consider sourcing better candidates."

    interview_rate = (summary.recommended_for_interview_count / summary.total_candidates) * 100
    if interview_rate >= 30:
        readiness = f"Excellent: {interview_rate:.0f}% of candidates ready for interview."
    elif interview_rate >= 15:
        readiness = f"Good: {interview_rate:.0f}% of candidates ready for interview."
    else:
        readiness = f"Limited: Only {interview_rate:.0f}% ready for interview."

    gap = (
        f"Most candidates lack: {summary.common_missing_skills[0]}"
        if summary.common_missing_skills
        else "No major skill gaps detected."
    )

    if summary.recommended_for_interview_count >= 3:
        recommendation = "Proceed with interviews for top candidates."
    elif summary.shortlisted_count >= 5:
        recommendation = "Consider expanding search or adjusting requirements."
    else:
        recommendation = "Recommend sourcing additional candidates."

    return {
        "pool_quality": pool_quality,
        "interview_readiness": readiness,
        "skill_gap": gap,
        "recommendation": recommendation,
    }


def _determine_recommendation(fit_score: int) -> str:
    if fit_score >= 75:
        return "Strong Hire"
    elif fit_score >= 55:
        return "Shortlisted"
    elif fit_score >= 40:
        return "Maybe"
    else:
        return "Not a Fit"


def _compute_score_distribution(scores: list[int]) -> dict[str, int]:
    distribution = {"excellent": 0, "good": 0, "moderate": 0, "poor": 0}
    for score in scores:
        if score >= 80:
            distribution["excellent"] += 1
        elif score >= 60:
            distribution["good"] += 1
        elif score >= 40:
            distribution["moderate"] += 1
        else:
            distribution["poor"] += 1
    return distribution


def _empty_summary() -> AnalyticsSummary:
    return AnalyticsSummary(
        total_candidates=0,
        average_fit_score=0.0,
        top_candidate_score=0,
        shortlisted_count=0,
        recommended_for_interview_count=0,
        common_missing_skills=(),
        score_distribution={"excellent": 0, "good": 0, "moderate": 0, "poor": 0},
        recommendation_breakdown={},
    )
