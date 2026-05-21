"""
Rule-based recruiter chatbot.
Answers hiring questions using real DB data — no external API required.
"""
from __future__ import annotations

import re
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.session import get_db
from db.models import Job, Application, Candidate, Interview

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)
    job_id: str | None = None


class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

def _intent(msg: str) -> str:
    m = msg.lower()
    if re.search(r"top|best|highest|rank|score", m) and re.search(r"candidate|applicant", m):
        return "top_candidates"
    if re.search(r"how many|count|total|number of", m) and re.search(r"candidate|applicant|application", m):
        return "count_candidates"
    if re.search(r"shortlist|who (should|to) (shortlist|interview|hire)", m):
        return "shortlist"
    if re.search(r"stage|pipeline|funnel|breakdown|status", m):
        return "pipeline_stages"
    if re.search(r"interview question|ask.*candidate|question.*for", m):
        return "interview_questions"
    if re.search(r"job description|jd|write.*job|create.*job", m):
        return "job_description"
    if re.search(r"analyze.*jd|check.*jd|is.*jd good|improve.*jd|jd.*good|jd.*bad|jd.*quality", m):
        return "jd_analysis"
    if re.search(r"offer letter|offer.*draft|draft.*offer", m):
        return "offer_letter"
    if re.search(r"missing skill|skill gap|lacking|don.t have", m):
        return "skill_gaps"
    if re.search(r"why.*reject|reason.*reject|reject.*reason", m):
        return "why_rejected"
    if re.search(r"improve.*resume|resume.*improve|fix.*resume|resume.*tips", m):
        return "improve_resume"
    if re.search(r"decision|should.*hire|hire.*decision|who.*hire", m):
        return "hiring_decision"
    if re.search(r"interview|scheduled|upcoming|meeting", m):
        return "interviews"
    if re.search(r"reject|not a fit|low score|poor", m):
        return "rejections"
    if re.search(r"job|position|role|opening|requisition", m):
        return "jobs_info"
    if re.search(r"hi|hello|hey|help|what can you|what do you", m):
        return "greeting"
    return "general"


# ---------------------------------------------------------------------------
# Handler helpers
# ---------------------------------------------------------------------------

async def _get_apps(db: AsyncSession, job_id: str | None) -> list[Application]:
    q = select(Application)
    if job_id:
        try:
            import uuid
            q = q.where(Application.job_id == uuid.UUID(job_id))
        except Exception:
            pass
    result = await db.execute(q)
    return list(result.scalars().all())


async def _get_candidate_name(db: AsyncSession, cid) -> str:
    c = await db.get(Candidate, cid)
    return c.full_name if c else str(cid)


async def _get_job(db: AsyncSession, job_id: str | None) -> Job | None:
    if not job_id:
        return None
    try:
        import uuid
        return await db.get(Job, uuid.UUID(job_id))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Intent handlers
# ---------------------------------------------------------------------------

async def _handle_top_candidates(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    if not apps:
        return "No applications found yet. Upload some resumes first to see ranked candidates."

    ranked = sorted(apps, key=lambda a: a.final_score or a.resume_score or 0, reverse=True)[:5]
    lines = ["**Top Candidates by Score:**\n"]
    for i, a in enumerate(ranked, 1):
        score = a.final_score or a.resume_score or 0
        name = await _get_candidate_name(db, a.candidate_id)
        skills = ", ".join((a.matched_skills or [])[:3]) or "—"
        lines.append(f"{i}. **{name}** — Score: {score:.0f}% | Stage: {a.stage} | Skills: {skills}")
    return "\n".join(lines)


async def _handle_count(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    active = [a for a in apps if a.status != "rejected"]
    rejected = [a for a in apps if a.status == "rejected"]
    return (
        f"**Application Summary:**\n"
        f"- Total applications: {len(apps)}\n"
        f"- Active: {len(active)}\n"
        f"- Rejected: {len(rejected)}\n"
        f"- Interview ready (score ≥ 70): {sum(1 for a in active if (a.final_score or a.resume_score or 0) >= 70)}"
    )


async def _handle_shortlist(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    if not apps:
        return "No applications found. Upload resumes to get shortlist recommendations."

    strong = [a for a in apps if (a.final_score or a.resume_score or 0) >= 70 and a.status != "rejected"]
    maybe  = [a for a in apps if 50 <= (a.final_score or a.resume_score or 0) < 70 and a.status != "rejected"]

    lines = ["**Shortlist Recommendation:**\n"]
    if strong:
        lines.append("✅ **Strong Hire (score ≥ 70%):**")
        for a in sorted(strong, key=lambda x: x.final_score or x.resume_score or 0, reverse=True)[:5]:
            name = await _get_candidate_name(db, a.candidate_id)
            score = a.final_score or a.resume_score or 0
            lines.append(f"  - {name} ({score:.0f}%)")
    if maybe:
        lines.append("\n🟡 **Consider (score 50–69%):**")
        for a in sorted(maybe, key=lambda x: x.final_score or x.resume_score or 0, reverse=True)[:3]:
            name = await _get_candidate_name(db, a.candidate_id)
            score = a.final_score or a.resume_score or 0
            lines.append(f"  - {name} ({score:.0f}%)")
    if not strong and not maybe:
        lines.append("No candidates meet the shortlist threshold yet. Consider lowering requirements or sourcing more candidates.")
    return "\n".join(lines)


async def _handle_pipeline(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    if not apps:
        return "No applications in the pipeline yet."

    stages = {}
    for a in apps:
        stages[a.stage] = stages.get(a.stage, 0) + 1

    order = ["applied", "shortlisted", "test_sent", "tested", "interview_1", "interview_2", "offered", "rejected"]
    lines = ["**Pipeline Breakdown:**\n"]
    for s in order:
        if s in stages:
            bar = "█" * min(stages[s], 10)
            lines.append(f"- {s.replace('_',' ').title()}: {stages[s]} {bar}")
    return "\n".join(lines)


async def _handle_skill_gaps(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    if not apps:
        return "No applications found to analyze skill gaps."

    from collections import Counter
    all_missing: list[str] = []
    for a in apps:
        all_missing.extend(a.missing_skills or [])

    if not all_missing:
        return "No skill gap data available yet. Upload and score resumes first."

    top = Counter(all_missing).most_common(7)
    lines = ["**Most Common Skill Gaps:**\n"]
    for skill, count in top:
        lines.append(f"- {skill}: missing in {count} candidate(s)")
    lines.append("\n💡 Consider adding training programs or adjusting job requirements for the top gaps.")
    return "\n".join(lines)


async def _handle_interviews(db: AsyncSession, job_id: str | None) -> str:
    q = select(Interview)
    if job_id:
        try:
            import uuid
            q = q.where(Interview.job_id == uuid.UUID(job_id))
        except Exception:
            pass
    result = await db.execute(q.order_by(Interview.scheduled_at.asc()).limit(10))
    interviews = list(result.scalars().all())

    if not interviews:
        return "No interviews scheduled yet. Go to the Pipeline page to schedule interviews."

    scheduled = [i for i in interviews if i.status == "scheduled"]
    completed = [i for i in interviews if i.status == "completed"]

    lines = [f"**Interviews Summary:**\n- Scheduled: {len(scheduled)}\n- Completed: {len(completed)}\n"]
    if scheduled:
        lines.append("**Upcoming:**")
        for iv in scheduled[:3]:
            dt = iv.scheduled_at.strftime("%d %b %Y %H:%M") if iv.scheduled_at else "TBD"
            lines.append(f"  - Round {iv.round_number} on {dt}")
    return "\n".join(lines)


async def _handle_jobs(db: AsyncSession) -> str:
    result = await db.execute(select(Job).order_by(Job.created_at.desc()).limit(10))
    jobs = list(result.scalars().all())
    if not jobs:
        return "No jobs created yet. Go to the Jobs page to create your first requisition."

    lines = ["**Active Jobs:**\n"]
    for j in jobs:
        lines.append(f"- **{j.title}** | Status: {j.status} | Deadline: {j.deadline.strftime('%d %b %Y') if j.deadline else 'None'}")
    return "\n".join(lines)


async def _handle_rejections(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    low = [a for a in apps if (a.final_score or a.resume_score or 0) < 40 and a.status != "rejected"]
    if not low:
        return "No candidates currently flagged for rejection (score < 40%)."
    lines = [f"**Candidates to Consider Rejecting (score < 40%):** {len(low)}\n"]
    for a in sorted(low, key=lambda x: x.final_score or x.resume_score or 0)[:5]:
        name = await _get_candidate_name(db, a.candidate_id)
        score = a.final_score or a.resume_score or 0
        lines.append(f"- {name} ({score:.0f}%)")
    return "\n".join(lines)


def _handle_interview_questions(msg: str) -> str:
    role = "the role"
    m = re.search(r"for\s+(?:a\s+)?(.+?)(?:\?|$)", msg, re.IGNORECASE)
    if m:
        role = m.group(1).strip()
    return (
        f"**Interview Questions for {role.title()}:**\n\n"
        "**Technical:**\n"
        f"1. Walk me through a challenging project you built using your core skills.\n"
        f"2. How do you approach debugging a production issue under pressure?\n"
        f"3. Describe your experience with system design and scalability.\n\n"
        "**Behavioural:**\n"
        "4. Tell me about a time you disagreed with a teammate. How did you resolve it?\n"
        "5. Describe a situation where you had to learn something quickly.\n"
        "6. How do you prioritise tasks when everything feels urgent?\n\n"
        "**Culture Fit:**\n"
        "7. Why are you interested in this role specifically?\n"
        "8. Where do you see yourself in 2 years?"
    )


def _handle_jd(msg: str) -> str:
    role = "Software Engineer"
    m = re.search(r"for\s+(?:a\s+)?(.+?)(?:\?|$)", msg, re.IGNORECASE)
    if m:
        role = m.group(1).strip().title()
    return (
        f"**Job Description Template — {role}:**\n\n"
        f"**About the Role:**\nWe are looking for a talented {role} to join our growing team. "
        f"You will work on challenging problems and collaborate with cross-functional teams.\n\n"
        "**Responsibilities:**\n"
        "- Design, build, and maintain high-quality software\n"
        "- Collaborate with product and design teams\n"
        "- Participate in code reviews and technical discussions\n"
        "- Contribute to architecture decisions\n\n"
        "**Requirements:**\n"
        "- 2+ years of relevant experience\n"
        "- Strong problem-solving skills\n"
        "- Experience with modern development practices (CI/CD, testing)\n"
        "- Excellent communication skills\n\n"
        "**Nice to Have:**\n"
        "- Open source contributions\n"
        "- Experience in a fast-paced startup environment"
    )


def _handle_offer_letter() -> str:
    return (
        "**Offer Letter Draft:**\n\n"
        "Dear [Candidate Name],\n\n"
        "We are delighted to offer you the position of **[Job Title]** at **[Company Name]**.\n\n"
        "**Offer Details:**\n"
        "- Position: [Job Title]\n"
        "- Start Date: [Date]\n"
        "- Compensation: [CTC/Salary]\n"
        "- Location: [Office/Remote]\n\n"
        "This offer is contingent upon successful completion of background verification.\n"
        "Please confirm your acceptance within **3 business days**.\n\n"
        "We look forward to welcoming you to the team!\n\n"
        "Warm regards,\n[HR Manager Name]\n[Company Name]"
    )


def _handle_greeting() -> str:
    return (
        "👋 Hi! I'm your **FairHire AI Assistant**.\n\n"
        "I can help you with:\n"
        "- 📊 **Top candidates** — ranked by score\n"
        "- 🔍 **Shortlist recommendations**\n"
        "- ✅ **Hiring decisions** — Strong Hire / Hire / Hold / Reject\n"
        "- 📈 **Pipeline breakdown** by stage\n"
        "- ⚠️ **Skill gap analysis**\n"
        "- ❓ **Why was a candidate rejected?**\n"
        "- 📝 **Resume improvement tips**\n"
        "- 🔎 **Analyze your JD** — type: *analyze jd: [paste JD]*\n"
        "- 📅 **Interview schedule**\n"
        "- 💌 **Offer letter** drafts\n\n"
        "What would you like to know?"
    )


def _handle_general(msg: str) -> str:
    return (
        "I can answer questions about your hiring pipeline. Try asking:\n\n"
        "- \"Who are the top candidates?\"\n"
        "- \"Show me the pipeline breakdown\"\n"
        "- \"Which candidates should I shortlist?\"\n"
        "- \"What are the common skill gaps?\"\n"
        "- \"Write interview questions for a backend developer\"\n"
        "- \"Draft a job description for a data scientist\""
    )


async def _handle_why_rejected(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    rejected = [a for a in apps if a.stage == "rejected" or a.status == "rejected"]
    if not rejected:
        return "No rejected candidates found for this job."
    lines = ["**Rejected Candidates & Reasons:**\n"]
    for a in rejected[:5]:
        name = await _get_candidate_name(db, a.candidate_id)
        score = a.final_score or a.resume_score or 0
        missing = ", ".join((a.missing_skills or [])[:3]) or "N/A"
        lines.append(f"- **{name}** — Score: {score:.0f}% | Missing: {missing}")
    return "\n".join(lines)


async def _handle_improve_resume(db: AsyncSession, job_id: str | None) -> str:
    apps = await _get_apps(db, job_id)
    if not apps:
        return "No candidates found. Upload resumes first."
    from collections import Counter
    all_missing: list[str] = []
    for a in apps:
        all_missing.extend(a.missing_skills or [])
    top_gaps = Counter(all_missing).most_common(5)
    lines = ["**Resume Improvement Tips for Candidates:**\n"]
    lines.append("Based on current applications, candidates should add:")
    for skill, count in top_gaps:
        lines.append(f"- **{skill}** — missing in {count} resume(s)")
    lines.append("\n**General Tips:**")
    lines.append("- Add quantified achievements (e.g. 'Reduced load time by 40%')")
    lines.append("- Include GitHub/LinkedIn profile links")
    lines.append("- List projects with tech stack used")
    lines.append("- Keep resume to 1-2 pages")
    return "\n".join(lines)


async def _handle_hiring_decision(db: AsyncSession, job_id: str | None) -> str:
    from services.decision_engine import make_decision
    apps = await _get_apps(db, job_id)
    if not apps:
        return "No applications found to make hiring decisions."
    active = [a for a in apps if a.stage not in ("rejected", "offered")]
    if not active:
        return "All candidates are already in final stages (offered/rejected)."
    lines = ["**Hiring Decisions:**\n"]
    ranked = sorted(active, key=lambda a: a.final_score or a.resume_score or 0, reverse=True)[:8]
    for a in ranked:
        name = await _get_candidate_name(db, a.candidate_id)
        d = make_decision(
            fit_score=a.final_score or a.resume_score or 0,
            matched_skills=a.matched_skills or [],
            missing_skills=a.missing_skills or [],
            test_score=a.test_score,
            interview_score=a.interview_score,
        )
        emoji = {"Strong Hire": "✅", "Hire": "🟢", "Hold": "🟡", "Reject": "🔴"}.get(d.decision, "⚪")
        lines.append(f"{emoji} **{name}** — {d.decision} | {d.next_action}")
    return "\n".join(lines)


def _handle_jd_analysis(msg: str) -> str:
    # Extract JD text from message if provided after a colon or newline
    jd_text = ""
    if ":" in msg:
        jd_text = msg.split(":", 1)[1].strip()
    if len(jd_text) < 30:
        return (
            "To analyze your JD, paste it like this:\n\n"
            "*analyze jd: [paste your full job description here]*\n\n"
            "I'll check for: length, missing sections, vague language, skill coverage, and salary info."
        )
    from services.jd_optimizer import analyze_jd
    result = analyze_jd(jd_text)
    lines = [f"**JD Analysis — {result['label']} ({result['score']}/100)**\n"]
    if result["issues"]:
        lines.append("**Issues Found:**")
        for issue in result["issues"]:
            lines.append(f"- ⚠️ {issue}")
    if result["suggestions"]:
        lines.append("\n**Suggestions:**")
        for s in result["suggestions"]:
            lines.append(f"- 💡 {s}")
    if result["skills_detected"]:
        lines.append(f"\n**Skills Detected:** {', '.join(result['skills_detected'][:8])}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    intent = _intent(req.message)

    if intent == "top_candidates":
        reply = await _handle_top_candidates(db, req.job_id)
    elif intent == "count_candidates":
        reply = await _handle_count(db, req.job_id)
    elif intent == "shortlist":
        reply = await _handle_shortlist(db, req.job_id)
    elif intent == "pipeline_stages":
        reply = await _handle_pipeline(db, req.job_id)
    elif intent == "skill_gaps":
        reply = await _handle_skill_gaps(db, req.job_id)
    elif intent == "interviews":
        reply = await _handle_interviews(db, req.job_id)
    elif intent == "rejections":
        reply = await _handle_rejections(db, req.job_id)
    elif intent == "why_rejected":
        reply = await _handle_why_rejected(db, req.job_id)
    elif intent == "improve_resume":
        reply = await _handle_improve_resume(db, req.job_id)
    elif intent == "hiring_decision":
        reply = await _handle_hiring_decision(db, req.job_id)
    elif intent == "jd_analysis":
        reply = _handle_jd_analysis(req.message)
    elif intent == "jobs_info":
        reply = await _handle_jobs(db)
    elif intent == "interview_questions":
        reply = _handle_interview_questions(req.message)
    elif intent == "job_description":
        reply = _handle_jd(req.message)
    elif intent == "offer_letter":
        reply = _handle_offer_letter()
    elif intent == "greeting":
        reply = _handle_greeting()
    else:
        reply = _handle_general(req.message)

    return ChatResponse(reply=reply)
