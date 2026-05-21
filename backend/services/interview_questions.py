"""
Stateless interview question generator.
Generates technical, HR, project, and skill-gap questions from a candidate profile.
"""
from __future__ import annotations


def generate_interview_questions(
    skills: tuple[str, ...],
    experience_years: int | None,
    missing_skills: tuple[str, ...],
) -> dict[str, list[str]]:
    return {
        "technical": _technical(skills),
        "hr": _hr(experience_years),
        "project": _project(skills),
        "skill_gap": _skill_gap(missing_skills),
    }


def _technical(skills: tuple[str, ...]) -> list[str]:
    questions = []
    for skill in skills[:5]:
        questions.append(f"Explain your experience with {skill}.")
        questions.append(f"What are advanced concepts in {skill}?")
    return questions


def _hr(exp: int | None) -> list[str]:
    questions = [
        "Tell me about yourself.",
        "Why do you want this role?",
        "Describe a challenging situation you handled.",
    ]
    if exp is not None and exp >= 3:
        questions.append("Describe a leadership experience.")
    else:
        questions.append("How do you handle learning new technologies quickly?")
    return questions


def _project(skills: tuple[str, ...]) -> list[str]:
    return [f"Describe a project where you used {skill}." for skill in skills[:3]]


def _skill_gap(missing_skills: tuple[str, ...]) -> list[str]:
    return [
        f"You don't have experience in {skill}. How would you learn it quickly?"
        for skill in missing_skills[:3]
    ]
