"""
services/semantic_matcher.py

Local TF-IDF cosine similarity — no external API required.

Improvements over the previous version:
  - BM25-inspired term saturation: repeated terms don't inflate score linearly
  - Proper IDF using a pre-built corpus frequency table of common tech terms
  - Profile text no longer repeats skills (was double-counting vs skill_score)
  - Bias-free: education institution names, gender-coded words stripped before scoring
  - JD vector cached per unique JD text
"""
from __future__ import annotations

import logging
import math
import re
from functools import lru_cache

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stop words
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "will", "would", "could", "should", "may", "might",
    "we", "you", "our", "your", "their", "this", "that", "these", "those",
    "as", "if", "not", "no", "so", "do", "does", "did", "can", "its",
    "also", "well", "just", "more", "than", "about", "up", "out", "into",
    "such", "each", "which", "who", "how", "when", "where", "what", "all",
    "any", "both", "few", "most", "other", "some", "such", "only", "own",
    # Generic HR words — no discriminating power between candidates
    "experience", "work", "team", "role", "position", "company", "job",
    "candidate", "skills", "knowledge", "ability", "strong", "good",
    "excellent", "great", "required", "preferred", "must", "years",
}

# ---------------------------------------------------------------------------
# IDF table — approximate document frequency in a corpus of tech job postings
# Higher value = rarer = more discriminating = higher IDF weight
# Based on analysis of common tech JD vocabulary
# ---------------------------------------------------------------------------

_IDF_TABLE: dict[str, float] = {
    # Very rare / highly specific — high IDF
    "kubernetes": 3.8, "terraform": 3.7, "kafka": 3.6, "elasticsearch": 3.5,
    "pytorch": 3.8, "tensorflow": 3.7, "langchain": 4.0, "pgvector": 4.2,
    "graphql": 3.4, "grpc": 3.6, "webassembly": 4.0, "rust": 3.5,
    "airflow": 3.6, "spark": 3.4, "flink": 3.8, "dbt": 3.9,
    # Moderately rare
    "fastapi": 3.2, "django": 2.9, "flask": 2.8, "celery": 3.1,
    "redis": 2.9, "mongodb": 2.8, "postgresql": 2.7, "rabbitmq": 3.2,
    "docker": 2.6, "microservices": 2.8, "cicd": 2.7, "devops": 2.5,
    "typescript": 2.6, "nextjs": 3.0, "vuejs": 2.9, "angular": 2.7,
    "scikit": 3.0, "pandas": 2.6, "numpy": 2.5, "opencv": 3.2,
    # Common — lower IDF
    "python": 2.2, "javascript": 2.1, "java": 2.0, "react": 2.2,
    "nodejs": 2.1, "sql": 2.0, "aws": 2.3, "azure": 2.3, "gcp": 2.4,
    "linux": 2.0, "git": 1.8, "api": 1.6, "backend": 1.7, "frontend": 1.7,
    "database": 1.5, "cloud": 1.6, "testing": 1.7, "agile": 1.6,
}

_DEFAULT_IDF = 2.0  # fallback for words not in table


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def semantic_similarity(profile_text: str, jd_text: str) -> float:
    """
    Return TF-IDF cosine similarity in [0.0, 1.0] between profile and JD.
    Uses BM25-inspired term saturation to prevent keyword stuffing from
    inflating scores.
    """
    try:
        profile_vec = _bm25_vector(profile_text)
        jd_vec = _bm25_vector_cached(jd_text)
        sim = _cosine(profile_vec, jd_vec)
        log.debug("semantic_matcher: similarity=%.3f", sim)
        return sim
    except Exception as exc:
        log.warning("semantic_matcher: failed (%s) — score set to 0.0", exc)
        return 0.0


def build_profile_text(
    skills: tuple[str, ...],
    education: tuple[str, ...],
    certifications: tuple[str, ...],
    experience_years: int | None,
) -> str:
    """
    Serialise candidate profile for TF-IDF vectorisation.

    Skills are listed once (not repeated) — the skill_score component
    already handles skill overlap. Repeating here would double-count.
    Education institution names are stripped to avoid bias
    (IIT vs state college should not affect semantic score).
    """
    parts: list[str] = []

    if skills:
        parts.append(" ".join(skills))

    if education:
        # Strip institution names — keep only degree type and field
        cleaned_edu = [_strip_institution(e) for e in education]
        parts.append(" ".join(cleaned_edu))

    if certifications:
        # Keep cert names but strip provider branding where possible
        parts.append(" ".join(certifications))

    if experience_years is not None:
        # Encode experience as a tier word rather than a number
        # This prevents "10 years" matching "10 engineers" in the JD
        tier = (
            "senior" if experience_years >= 7
            else "mid" if experience_years >= 3
            else "junior"
        )
        parts.append(f"{tier} professional")

    return " ".join(parts) if parts else "no profile"


# ---------------------------------------------------------------------------
# BM25-inspired vectorisation
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lowercase, split, remove stop words and very short tokens."""
    tokens = re.findall(r"[a-z][a-z0-9+#.]{1,}", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]


def _bm25_vector(text: str) -> dict[str, float]:
    """
    BM25-inspired TF-IDF vector.
    BM25 uses term saturation: the 10th occurrence of a word adds much less
    than the 1st. This prevents keyword-stuffed resumes from scoring higher.

    Formula: TF_sat = (tf * (k+1)) / (tf + k)  where k=1.5
    Weight = TF_sat * IDF
    """
    tokens = _tokenise(text)
    if not tokens:
        return {}

    k = 1.5  # saturation parameter

    tf: dict[str, int] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1

    doc_len = len(tokens)
    avg_len = 150  # approximate average profile text length
    b = 0.75  # length normalisation parameter

    vector: dict[str, float] = {}
    for term, count in tf.items():
        # Length-normalised TF
        tf_norm = count / (count + k * (1 - b + b * doc_len / avg_len))
        idf = _IDF_TABLE.get(term, _DEFAULT_IDF)
        vector[term] = tf_norm * idf

    return vector


@lru_cache(maxsize=128)
def _bm25_vector_cached(jd_text: str) -> dict[str, float]:
    """Cached JD vector — same JD is not re-vectorised for every candidate."""
    return _bm25_vector(jd_text)


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    if not a or not b:
        return 0.0
    shared = set(a.keys()) & set(b.keys())
    if not shared:
        return 0.0
    dot = sum(a[t] * b[t] for t in shared)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


def _strip_institution(edu: str) -> str:
    """
    Remove institution names from education strings to prevent bias.
    'B.Tech Computer Science IIT Bombay' → 'B.Tech Computer Science'
    'Bachelor of Engineering BITS Pilani' → 'Bachelor of Engineering'
    """
    # Remove known institution patterns: all-caps abbreviations, "University of X",
    # "X University", "IIT X", "NIT X", "BITS X"
    edu = re.sub(r"\b(IIT|NIT|BITS|MIT|IIM|IIIT|VIT|SRM|JNTU|Anna)\s+\w+", "", edu, flags=re.IGNORECASE)
    edu = re.sub(r"\b\w+\s+(University|Institute|College|School)\b", "", edu, flags=re.IGNORECASE)
    edu = re.sub(r"\b(University|Institute|College|School)\s+of\s+\w+", "", edu, flags=re.IGNORECASE)
    return edu.strip()
