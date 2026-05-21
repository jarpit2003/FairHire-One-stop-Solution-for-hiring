"""
services/scoring_service.py

Deterministic impact scoring — no external API required.

Design principles (matching real ATS systems like Workday, Greenhouse):
  - Bias-free: scores are based purely on what is written, not who wrote it
  - Calibrated: a score of 70 means the same thing across all candidates
  - Transparent: every point added or deducted has a clear reason
  - Penalise vagueness, reward specificity and measurable outcomes

Scoring rubric per sentence (0–10):
  Quantified outcome with strong unit  (+4)   "reduced latency by 40%"
  Quantified outcome with weak unit    (+2)   "worked on 3 projects"
  Strong leadership/delivery verb      (+2)   "led", "architected", "scaled"
  JD domain keyword match              (+1 each, max 3)
  Sentence is specific (≥12 words)     (+1)
  Weak filler phrase present           (-3)   "responsible for", "helped with"
  No action verb at all                (-1)
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Strong quantified outcomes — number + meaningful unit
# These indicate real business impact (%, x multiplier, time saved, scale)
_STRONG_QUANT = re.compile(
    r"\d+\s*(%|x\b|times\b|ms\b|seconds?\b|minutes?\b|hours?\b|days?\b"
    r"|million\b|billion\b|tb\b|gb\b|mb\b"
    r"|users?\b|customers?\b|clients?\b|transactions?\b|requests?\b"
    r"|revenue\b|cost\b|budget\b|saving\b|savings\b)",
    re.IGNORECASE,
)

# Weak quantified — number + vague unit (still better than nothing)
_WEAK_QUANT = re.compile(
    r"\d+\s*(projects?\b|tasks?\b|features?\b|bugs?\b|tickets?\b"
    r"|repos?\b|services?\b|apis?\b|endpoints?\b|lines?\b|modules?\b"
    r"|teams?\b|members?\b|engineers?\b)",
    re.IGNORECASE,
)

# High-signal verbs — leadership, ownership, measurable delivery
_STRONG_VERBS = re.compile(
    r"\b(led|owned|architected|spearheaded|drove|scaled|launched|shipped"
    r"|reduced|increased|improved|optimised|optimized|automated|migrated"
    r"|saved|generated|grew|cut|boosted|deployed|refactored|established"
    r"|designed|built|created|delivered|implemented|managed|developed)\\b",
    re.IGNORECASE,
)

# Weak filler — vague, passive, non-specific language
# These are the phrases that real ATS systems flag as low-quality
_WEAK_PHRASES = re.compile(
    r"\b(responsible for|worked on|helped with|assisted in|involved in"
    r"|participated in|exposure to|familiar with|knowledge of|part of"
    r"|contributed to|supported the|member of the|worked as part)\\b",
    re.IGNORECASE,
)

# Achievement sentence detector — must have at least one action verb to qualify
_ACHIEVEMENT_RE = re.compile(
    r"\b(reduc\w+|increas\w+|improv\w+|optimis\w+|optimiz\w+|achiev\w+"
    r"|deliver\w+|built|developed|designed|led|managed|launched|shipped"
    r"|scaled|automated|saved|generated|grew|cut|boosted|deployed"
    r"|migrated|refactor\w+|architected|owned|drove|spearheaded"
    r"|implemented|created|established)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def score_impact(resume_text: str, jd_text: str) -> tuple[float, list[str]]:
    """
    Deterministic impact scorer — no external API.
    Returns (impact_score 0.0–1.0, top 3 achievement sentences).

    Scoring is relative to the candidate's own resume, not absolute.
    This prevents bias: a fresher with 2 strong sentences scores fairly
    against a senior with 10 mediocre ones.
    """
    sentences = _extract_achievement_sentences(resume_text)
    if not sentences:
        log.debug("impact_scorer: no achievement sentences found")
        return 0.0, []

    jd_keywords = _extract_jd_keywords(jd_text)
    scored = [(_score_sentence(s, jd_keywords), s) for s in sentences]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Use mean of ALL sentences, not just top-5
    # This prevents gaming by padding resumes with filler
    all_scores = [s for s, _ in scored]
    mean_score = sum(all_scores) / len(all_scores)

    # Bonus: if top sentence is excellent (≥8), reward the candidate
    top_score = scored[0][0] if scored else 0.0
    excellence_bonus = 0.5 if top_score >= 8.0 else 0.0

    raw = mean_score + excellence_bonus
    impact_score = round(min(max(raw / 10.0, 0.0), 1.0), 4)

    highlights = [sent for _, sent in scored[:3]]
    log.debug("impact_scorer: score=%.3f sentences=%d", impact_score, len(sentences))
    return impact_score, highlights


# ---------------------------------------------------------------------------
# Sentence scoring
# ---------------------------------------------------------------------------

def _score_sentence(sentence: str, jd_keywords: set[str]) -> float:
    """Score a single achievement sentence 0–10."""
    score = 0.0

    # Strong quantified outcome = +4 pts
    strong_quant = len(_STRONG_QUANT.findall(sentence))
    score += min(strong_quant * 4.0, 4.0)

    # Weak quantified outcome = +2 pts (only if no strong quant already)
    if strong_quant == 0:
        weak_quant = len(_WEAK_QUANT.findall(sentence))
        score += min(weak_quant * 2.0, 2.0)

    # Strong action verb = +2 pts
    if _STRONG_VERBS.search(sentence):
        score += 2.0

    # JD domain keyword match = +1 pt each (max 3)
    # Only count words ≥4 chars to avoid noise from short words
    sentence_lower = sentence.lower()
    jd_hits = sum(1 for kw in jd_keywords if len(kw) >= 4 and kw in sentence_lower)
    score += min(jd_hits * 1.0, 3.0)

    # Specificity bonus — longer sentences tend to be more specific
    words = len(sentence.split())
    if words >= 12:
        score += 1.0

    # Weak filler phrase = -3 pts (strong penalty — these are red flags)
    if _WEAK_PHRASES.search(sentence):
        score -= 3.0

    return max(0.0, min(score, 10.0))


def _extract_achievement_sentences(text: str) -> list[str]:
    """Split resume text into sentences and keep only achievement-signal ones."""
    # Split on sentence boundaries AND newlines (resume bullet points)
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    results: list[str] = []
    seen: set[str] = set()
    for s in raw_sentences:
        s = s.strip().lstrip("-•·*▪▸► ")
        if len(s) < 15:
            continue
        # Deduplicate near-identical sentences
        key = s[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        if _ACHIEVEMENT_RE.search(s):
            results.append(s)
    return results


def _extract_jd_keywords(jd_text: str) -> set[str]:
    """
    Extract meaningful domain words from JD for overlap scoring.
    Filters aggressively — only keeps words that carry real signal.
    """
    _STOP = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "will", "would", "could", "should", "may", "might",
        "we", "you", "our", "your", "their", "this", "that", "these", "those",
        "as", "if", "not", "no", "so", "do", "does", "did", "can", "its",
        # Generic HR filler — no signal value
        "experience", "required", "preferred", "must", "ability", "strong",
        "good", "excellent", "great", "work", "team", "role", "position",
        "candidate", "looking", "seeking", "join", "company", "opportunity",
        "skills", "knowledge", "understanding", "background", "proven",
        "plus", "bonus", "nice", "have", "years", "year", "minimum",
    }
    words = re.findall(r"[a-z][a-z0-9+#.]{2,}", jd_text.lower())
    return {w for w in words if w not in _STOP}
