from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.jd_matcher import MatchResult, match_candidate_to_jd
from services.profile_extractor import CandidateProfile

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CandidateProfileRequest(BaseModel):
    skills: list[str]
    education: list[str]
    certifications: list[str]
    experience_years: int | None = None
    resume_text: str = ""   # full resume text — enables impact scoring


class MatchRequest(BaseModel):
    candidate_profile: CandidateProfileRequest
    job_description: str = Field(..., min_length=10, max_length=50000)


class MatchResponse(BaseModel):
    fit_score: int = Field(..., ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    skill_overlap_score: float = Field(..., ge=0.0, le=1.0)
    education_relevance_score: float = Field(..., ge=0.0, le=1.0)
    experience_relevance_score: float = Field(..., ge=0.0, le=1.0)
    certification_score: float = Field(..., ge=0.0, le=1.0)
    semantic_similarity_score: float = Field(..., ge=0.0, le=1.0)
    impact_score: float = Field(..., ge=0.0, le=1.0)
    impact_highlights: list[str] = Field(..., description="Top achievement sentences from resume")
    score_components: dict[str, float] = Field(default_factory=dict, description="Raw component scores for storage")
    explanation: dict[str, str]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/jd",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Match candidate profile against job description",
    description=(
        "Computes fit score using impact (40%) + semantic (30%) + "
        "skill overlap (20%) + experience (10%). "
        "Pass resume_text for impact scoring; omitting it falls back to "
        "skill/semantic weights only."
    ),
)
async def match_jd(request: MatchRequest) -> MatchResponse:
    try:
        profile = CandidateProfile(
            skills=tuple(request.candidate_profile.skills),
            education=tuple(request.candidate_profile.education),
            certifications=tuple(request.candidate_profile.certifications),
            experience_years=request.candidate_profile.experience_years,
        )
        result = await match_candidate_to_jd(
            profile,
            request.job_description,
            resume_text=request.candidate_profile.resume_text,
        )
        return MatchResponse(
            fit_score=result.fit_score,
            matched_skills=list(result.matched_skills),
            missing_skills=list(result.missing_skills),
            skill_overlap_score=result.skill_overlap_score,
            education_relevance_score=result.education_relevance_score,
            experience_relevance_score=result.experience_relevance_score,
            certification_score=result.certification_score,
            semantic_similarity_score=result.semantic_similarity_score,
            impact_score=result.impact_score,
            impact_highlights=list(result.impact_highlights),
            score_components={
                "impact":     round(result.impact_score, 4),
                "semantic":   round(result.semantic_similarity_score, 4),
                "skill":      round(result.skill_overlap_score, 4),
                "cert":       round(result.certification_score, 4),
                "experience": round(result.experience_relevance_score, 4),
            },
            explanation=_generate_explanation(result),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


# ---------------------------------------------------------------------------
# Explanation helper
# ---------------------------------------------------------------------------

def _generate_explanation(result: MatchResult) -> dict[str, str]:
    matched_count = len(result.matched_skills)
    total_jd      = matched_count + len(result.missing_skills)
    exp: dict[str, str] = {}

    # Impact
    if result.impact_score > 0.0:
        exp["impact"] = (
            f"Impact score {result.impact_score:.0%} — "
            f"{len(result.impact_highlights)} key achievements identified"
        )
    else:
        exp["impact"] = "No quantified achievements found — score based on skills and semantics"

    # Skills
    exp["skill_match"] = (
        f"{matched_count}/{total_jd} required skills matched ({result.skill_overlap_score:.0%} overlap)"
        if total_jd else "No specific skills identified in JD"
    )

    # Semantic
    exp["semantic_match"] = (
        f"Semantic similarity {result.semantic_similarity_score:.0%}"
        if result.semantic_similarity_score > 0.0
        else "Semantic scoring unavailable — deterministic fallback applied"
    )

    # Experience
    exp["experience"] = (
        "Meets or exceeds experience requirements"   if result.experience_relevance_score >= 0.8
        else "Partially meets experience requirements" if result.experience_relevance_score >= 0.5
        else "Below typical experience requirements"
    )

    # Overall
    exp["overall"] = (
        "Excellent fit — highly recommended"        if result.fit_score >= 80
        else "Good fit — recommended for interview" if result.fit_score >= 60
        else "Moderate fit — consider for screening" if result.fit_score >= 40
        else "Limited fit"
    )
    return exp
