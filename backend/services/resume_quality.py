"""
Resume quality scorer.
Evaluates how well-written a resume is — independent of job fit.
Returns a score 0-100 with a breakdown.
"""
from __future__ import annotations
import re


_ACHIEVEMENT_WORDS = re.compile(
    r"\b(achieved|delivered|built|launched|improved|reduced|increased|led|"
    r"designed|developed|optimised|optimized|saved|generated|scaled|automated)\b",
    re.IGNORECASE,
)

_QUANTIFIED = re.compile(r"\d+\s*(%|x|times|users|ms|seconds|hours|days|k\b|million|billion)", re.IGNORECASE)


def compute_resume_quality(text: str) -> dict:
    """
    Returns a quality dict with total score (0-100) and per-dimension breakdown.
    """
    words = text.split()
    word_count = len(words)
    breakdown: dict[str, int] = {}

    # 1. Length — a good resume has 300-800 words
    if word_count >= 600:
        breakdown["length"] = 20
    elif word_count >= 300:
        breakdown["length"] = 15
    elif word_count >= 150:
        breakdown["length"] = 8
    else:
        breakdown["length"] = 0

    # 2. Has projects section
    breakdown["has_projects"] = 15 if re.search(r"\bprojects?\b", text, re.IGNORECASE) else 0

    # 3. Has experience section
    breakdown["has_experience"] = 15 if re.search(r"\b(experience|internship|employment)\b", text, re.IGNORECASE) else 0

    # 4. Has GitHub or portfolio link
    breakdown["has_links"] = 15 if re.search(r"github\.com|linkedin\.com|portfolio|behance", text, re.IGNORECASE) else 0

    # 5. Uses achievement-oriented language
    achievement_count = len(_ACHIEVEMENT_WORDS.findall(text))
    if achievement_count >= 5:
        breakdown["achievement_language"] = 20
    elif achievement_count >= 2:
        breakdown["achievement_language"] = 12
    else:
        breakdown["achievement_language"] = 0

    # 6. Has quantified results (numbers + units)
    quant_count = len(_QUANTIFIED.findall(text))
    if quant_count >= 3:
        breakdown["quantified_results"] = 15
    elif quant_count >= 1:
        breakdown["quantified_results"] = 8
    else:
        breakdown["quantified_results"] = 0

    total = min(sum(breakdown.values()), 100)

    if total >= 80:
        label = "Excellent"
    elif total >= 60:
        label = "Good"
    elif total >= 40:
        label = "Average"
    else:
        label = "Needs Improvement"

    return {
        "score": total,
        "label": label,
        "breakdown": breakdown,
        "word_count": word_count,
    }
