"""
JD Optimizer — analyzes a job description and returns improvement suggestions.
Used by the chatbot and can be exposed as an API endpoint.
"""
from __future__ import annotations
import re
from services.skill_taxonomy import SKILL_TAXONOMY


_VAGUE_WORDS = re.compile(
    r"\b(good|great|excellent|strong|passionate|ninja|rockstar|guru|wizard|dynamic|motivated)\b",
    re.IGNORECASE,
)

_REQUIRED_SECTIONS = {
    "responsibilities": re.compile(r"\b(responsibilit|duties|you will|role involves)\b", re.IGNORECASE),
    "requirements":     re.compile(r"\b(requirement|qualification|must have|you need|we need)\b", re.IGNORECASE),
    "experience":       re.compile(r"\b(\d+\+?\s*years?|experience)\b", re.IGNORECASE),
}


def analyze_jd(jd_text: str) -> dict:
    """
    Returns a quality score (0-100), issues list, and suggestions.
    """
    issues: list[str] = []
    suggestions: list[str] = []
    score = 100
    words = jd_text.split()

    # 1. Length check
    if len(words) < 50:
        issues.append("JD is too short (< 50 words). Candidates won't have enough info.")
        suggestions.append("Add responsibilities, requirements, and company description.")
        score -= 30
    elif len(words) < 150:
        issues.append("JD is brief. Consider adding more detail.")
        suggestions.append("Aim for 200-500 words for best candidate response.")
        score -= 15

    # 2. Missing sections
    for section, pattern in _REQUIRED_SECTIONS.items():
        if not pattern.search(jd_text):
            issues.append(f"Missing '{section}' section.")
            suggestions.append(f"Add a clear '{section.title()}' section.")
            score -= 10

    # 3. Vague language
    vague = _VAGUE_WORDS.findall(jd_text)
    if vague:
        unique_vague = list(set(w.lower() for w in vague))
        issues.append(f"Vague words found: {', '.join(unique_vague)}. These reduce quality applicants.")
        suggestions.append("Replace vague adjectives with specific skills and measurable expectations.")
        score -= len(unique_vague) * 3

    # 4. No skills mentioned
    mentioned_skills = [s for s, aliases in SKILL_TAXONOMY.items()
                        if any(a.lower() in jd_text.lower() for a in aliases if not a.startswith(r"\b"))]
    if len(mentioned_skills) == 0:
        issues.append("No specific technical skills mentioned.")
        suggestions.append("Add required skills like Python, React, Docker, etc.")
        score -= 20
    elif len(mentioned_skills) < 3:
        issues.append(f"Only {len(mentioned_skills)} skill(s) mentioned. Consider adding more.")
        suggestions.append("List at least 5 required skills for better candidate matching.")
        score -= 10

    # 5. No salary/compensation info
    if not re.search(r"\b(salary|compensation|ctc|lpa|lakh|pay|stipend|\$|€|£)\b", jd_text, re.IGNORECASE):
        issues.append("No compensation info. JDs with salary ranges get 30% more applicants.")
        suggestions.append("Add a salary range or 'Competitive compensation' at minimum.")
        score -= 5

    score = max(0, score)

    if score >= 80:
        label = "Good JD"
    elif score >= 60:
        label = "Needs Minor Improvements"
    elif score >= 40:
        label = "Needs Major Improvements"
    else:
        label = "Poor JD — Rewrite Recommended"

    return {
        "score": score,
        "label": label,
        "issues": issues,
        "suggestions": suggestions,
        "skills_detected": mentioned_skills,
        "word_count": len(words),
    }
