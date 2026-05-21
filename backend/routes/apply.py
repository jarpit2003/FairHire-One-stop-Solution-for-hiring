"""
routes/apply.py

GET  /apply/{job_id}        — public HTML application form
POST /apply/{job_id}/submit — form submission handler
"""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Job
from routes.intake import intake_submit, IntakeSubmission

router = APIRouter()


def _form_html(job_title: str, job_id: str, message: str = "", error: str = "") -> str:
    msg_html = f'<div class="success">{message}</div>' if message else ""
    err_html = f'<div class="error">{error}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apply — {job_title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0fdf4; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
  .card {{ background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 40px; width: 100%; max-width: 600px; }}
  .logo {{ color: #059669; font-size: 13px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }}
  h1 {{ font-size: 22px; font-weight: 700; color: #111; margin-bottom: 4px; }}
  .subtitle {{ font-size: 14px; color: #6b7280; margin-bottom: 28px; }}
  label {{ display: block; font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 6px; }}
  input, textarea {{ width: 100%; padding: 10px 14px; border: 1.5px solid #e5e7eb; border-radius: 8px; font-size: 14px; color: #111; outline: none; transition: border-color 0.2s; margin-bottom: 18px; font-family: inherit; }}
  input:focus, textarea:focus {{ border-color: #059669; }}
  textarea {{ resize: vertical; min-height: 160px; }}
  .optional {{ font-weight: 400; color: #9ca3af; }}
  button {{ width: 100%; padding: 12px; background: #059669; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
  button:hover {{ background: #047857; }}
  .success {{ background: #d1fae5; border: 1px solid #6ee7b7; color: #065f46; padding: 14px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }}
  .error {{ background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; padding: 14px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }}
  .required {{ color: #ef4444; }}
</style>
</head>
<body>
<div class="card">
  <div class="logo">QuantumLogic Labs</div>
  <h1>Apply for {job_title}</h1>
  <p class="subtitle">Fill in the form below and we'll get back to you within 5–7 business days.</p>
  {msg_html}{err_html}
  <form method="POST" action="/apply/{job_id}/submit">
    <label>Full Name <span class="required">*</span></label>
    <input type="text" name="full_name" required placeholder="e.g. John Doe" />

    <label>Email Address <span class="required">*</span></label>
    <input type="email" name="email" required placeholder="you@example.com" />

    <label>Phone Number <span class="optional">(optional)</span></label>
    <input type="text" name="phone" placeholder="e.g. 9876543210" />

    <label>LinkedIn URL <span class="optional">(optional)</span></label>
    <input type="url" name="linkedin_url" placeholder="https://linkedin.com/in/yourprofile" />

    <label>Resume / CV <span class="required">*</span></label>
    <textarea name="resume_text" required placeholder="Paste your full resume text here — skills, experience, education, certifications..."></textarea>

    <label>Cover Note <span class="optional">(optional)</span></label>
    <textarea name="cover_note" style="min-height:80px" placeholder="Why are you interested in this role?"></textarea>

    <button type="submit">Submit Application →</button>
  </form>
</div>
</body>
</html>"""


@router.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job: Job | None = await db.get(Job, job_id)
    title = job.title if job else "Position"
    return HTMLResponse(_form_html(title, str(job_id)))


@router.post("/apply/{job_id}/submit", response_class=HTMLResponse)
async def apply_submit(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    linkedin_url: str = Form(None),
    resume_text: str = Form(None),
    cover_note: str = Form(None),
):
    job: Job | None = await db.get(Job, job_id)
    title = job.title if job else "Position"
    try:
        body = IntakeSubmission(
            job_id=job_id,
            full_name=full_name,
            email=email,
            phone=phone or None,
            linkedin_url=linkedin_url or None,
            resume_text=resume_text or None,
            cover_note=cover_note or None,
        )
        await intake_submit(body, db)
        return HTMLResponse(_form_html(title, str(job_id),
            message=f"✅ Thank you {full_name}! Your application has been received. We'll be in touch soon."))
    except Exception as exc:
        return HTMLResponse(_form_html(title, str(job_id),
            error=f"Submission failed: {str(exc)}"))
