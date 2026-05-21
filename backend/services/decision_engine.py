"""
Hiring Decision Engine.
Makes a structured hire/hold/reject decision based on all available scores.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class HiringDecision:
    decision: str        # Strong Hire | Hire | Hold | Reject
    confidence: str      # High | Medium | Low
    reason: str
    next_action: str


def make_decision(
    fit_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    test_score: float | None = None,
    interview_score: float | None = None,
    experience_years: int | None = None,
) -> HiringDecision:
    """
    Makes a hiring decision based on all available data points.
    Uses whichever scores are available — gracefully handles missing data.
    """
    # Compute composite score from available signals
    scores: list[float] = [fit_score]
    weights: list[float] = [1.0]

    if test_score is not None:
        scores.append(test_score)
        weights.append(0.8)

    if interview_score is not None:
        scores.append(interview_score)
        weights.append(1.2)  # interview score weighted higher

    composite = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

    skill_coverage = len(matched_skills) / max(len(matched_skills) + len(missing_skills), 1)
    critical_missing = len(missing_skills)

    # Decision logic
    if composite >= 80 and skill_coverage >= 0.7:
        return HiringDecision(
            decision="Strong Hire",
            confidence="High",
            reason=f"Composite score {composite:.0f}%, strong skill match ({len(matched_skills)} skills matched).",
            next_action="Send offer letter immediately.",
        )

    if composite >= 65 and skill_coverage >= 0.5:
        return HiringDecision(
            decision="Hire",
            confidence="Medium" if critical_missing > 2 else "High",
            reason=f"Good fit score {composite:.0f}%. Missing {critical_missing} skill(s): {', '.join(missing_skills[:3]) or 'none'}.",
            next_action="Proceed to final interview round.",
        )

    if composite >= 50:
        return HiringDecision(
            decision="Hold",
            confidence="Medium",
            reason=f"Average score {composite:.0f}%. Skill gaps present: {', '.join(missing_skills[:3]) or 'none'}.",
            next_action="Consider for future openings or conduct one more assessment.",
        )

    return HiringDecision(
        decision="Reject",
        confidence="High" if composite < 35 else "Medium",
        reason=f"Low fit score {composite:.0f}%. Too many missing skills ({critical_missing}).",
        next_action="Send polite rejection email.",
    )


def bulk_decisions(applications: list[dict]) -> list[dict]:
    """Run decision engine on a list of application dicts."""
    results = []
    for app in applications:
        decision = make_decision(
            fit_score=app.get("resume_score") or app.get("final_score") or 0,
            matched_skills=app.get("matched_skills") or [],
            missing_skills=app.get("missing_skills") or [],
            test_score=app.get("test_score"),
            interview_score=app.get("interview_score"),
        )
        results.append({
            "candidate_id": app.get("candidate_id"),
            "candidate_name": app.get("candidate_name"),
            "decision": decision.decision,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "next_action": decision.next_action,
        })
    # Sort: Strong Hire first, then Hire, Hold, Reject
    order = {"Strong Hire": 0, "Hire": 1, "Hold": 2, "Reject": 3}
    return sorted(results, key=lambda x: order.get(x["decision"], 4))
