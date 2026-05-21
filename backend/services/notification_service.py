"""
services/notification_service.py

Email via Brevo (primary) → Resend (fallback) → SMTP (last resort).
Brevo free tier: 300 emails/day, sends to ANY address, no domain needed.
"""
from __future__ import annotations

import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core send — Brevo → Resend → SMTP
# ---------------------------------------------------------------------------

async def _send_email(to_email: str, subject: str, html: str) -> bool:
    if not to_email or "fairhire.local" in to_email:
        log.info("Skipping placeholder email: %s", to_email)
        return False

    if settings.BREVO_API_KEY:
        return await _send_via_brevo(to_email, subject, html)

    if settings.RESEND_API_KEY:
        return await _send_via_resend(to_email, subject, html)

    if settings.SMTP_ENABLED and settings.SMTP_USERNAME:
        return await _send_via_smtp(to_email, subject, html)

    log.warning("No email provider configured — set BREVO_API_KEY in .env")
    return False


async def _send_via_brevo(to_email: str, subject: str, html: str) -> bool:
    """Brevo REST API — sends to any email, no domain verification needed."""
    try:
        import requests
        import urllib3
        urllib3.disable_warnings()

        resp = await asyncio.get_running_loop().run_in_executor(None, lambda: requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "sender": {
                    "name": settings.BREVO_FROM_NAME,
                    "email": settings.BREVO_FROM_EMAIL,
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html,
            },
            verify=False,
            timeout=15,
        ))

        if resp.status_code in (200, 201):
            log.info("[Brevo] Sent '%s' to %s", subject, to_email)
            return True
        log.error("[Brevo] %s: %s", resp.status_code, resp.text)
        return False
    except Exception as e:
        log.error("[Brevo] Failed: %s", e)
        return False


async def _send_via_resend(to_email: str, subject: str, html: str) -> bool:
    """Resend fallback — only works for verified emails on free tier."""
    try:
        import requests
        import urllib3
        urllib3.disable_warnings()

        resp = await asyncio.get_running_loop().run_in_executor(None, lambda: requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            },
            verify=False,
            timeout=15,
        ))

        if resp.status_code in (200, 201):
            log.info("[Resend] Sent '%s' to %s", subject, to_email)
            return True
        log.error("[Resend] %s: %s", resp.status_code, resp.text)
        return False
    except Exception as e:
        log.error("[Resend] Failed: %s", e)
        return False


async def _send_via_smtp(to_email: str, subject: str, html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))
        await asyncio.get_running_loop().run_in_executor(None, _smtp_sync, msg, to_email)
        log.info("[SMTP] Sent '%s' to %s", subject, to_email)
        return True
    except Exception as e:
        log.error("[SMTP] Failed: %s", e)
        return False


def _smtp_sync(msg: MIMEMultipart, to_email: str) -> None:
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
        s.starttls()
        s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        s.send_message(msg)


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

def _base(content: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
      <div style="background:#059669;padding:24px;">
        <h1 style="color:white;margin:0;font-size:20px;">FairHire AI</h1>
      </div>
      <div style="padding:32px;">{content}</div>
      <div style="padding:16px 32px;background:#f1f5f9;font-size:12px;color:#94a3b8;">
        Automated message from FairHire AI.
      </div>
    </div>"""


async def send_application_acknowledgement(candidate_email: str, candidate_name: str, job_title: str) -> bool:
    html = _base(f"""
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Thank you for applying to <strong>{job_title}</strong> at FairHire AI.</p>
        <p>We will be in touch within 5–7 business days.</p>
        <p>Best regards,<br><strong>FairHire AI Recruitment Team</strong></p>""")
    return await _send_email(candidate_email, f"Application Received — {job_title}", html)


async def send_test_link(candidate_email: str, candidate_name: str, job_title: str,
                          test_link: str, deadline: str | None = None) -> bool:
    deadline_line = f"<p>Please complete by: <strong>{deadline}</strong></p>" if deadline else ""
    html = _base(f"""
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>You have been shortlisted for <strong>{job_title}</strong>. Please complete the assessment below.</p>
        {deadline_line}
        <div style="text-align:center;margin:32px 0;">
          <a href="{test_link}" style="background:#2563eb;color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;">Start Assessment →</a>
        </div>
        <p style="font-size:13px;color:#94a3b8;">Link: {test_link}</p>""")
    return await _send_email(candidate_email, f"Assessment Test — {job_title}", html)


async def send_interview_confirmation(candidate_email: str, candidate_name: str, job_title: str,
                                       interview_date: str, interview_time: str,
                                       meet_link: str | None = None, notes: str | None = None) -> bool:
    meet_section = f"<p>Meeting link: <a href='{meet_link}'>{meet_link}</a></p>" if meet_link else ""
    notes_section = f"<p><strong>Notes:</strong> {notes}</p>" if notes else ""
    html = _base(f"""
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>You have been invited for an interview for <strong>{job_title}</strong>.</p>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:8px;padding:20px;margin:20px 0;">
          <p style="margin:0 0 8px;"><strong>Date:</strong> {interview_date}</p>
          <p style="margin:0;"><strong>Time:</strong> {interview_time}</p>
        </div>
        {meet_section}{notes_section}
        <p>Please confirm your availability by replying to this email.</p>""")
    return await _send_email(candidate_email, f"Interview Scheduled — {job_title}", html)


async def send_rejection(candidate_email: str, candidate_name: str, job_title: str) -> bool:
    html = _base(f"""
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Thank you for your interest in <strong>{job_title}</strong> at FairHire AI.</p>
        <p>After careful consideration, we have decided to move forward with other candidates.</p>
        <p>We encourage you to apply for future openings.</p>
        <p>Best regards,<br><strong>FairHire AI Recruitment Team</strong></p>""")
    return await _send_email(candidate_email, f"Application Update — {job_title}", html)


async def send_offer(candidate_email: str, candidate_name: str, job_title: str, draft: str | None = None) -> bool:
    body = draft.replace("\n", "<br>") if draft and len(draft.strip()) > 50 else f"""
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Congratulations! We are delighted to extend an offer for <strong>{job_title}</strong> at FairHire AI.</p>
        <p>Our HR team will be in touch with the formal offer letter and next steps.</p>
        <p>Welcome to the team!<br><strong>FairHire AI Recruitment Team</strong></p>"""
    return await _send_email(candidate_email, f"Offer Letter — {job_title}", _base(body))


async def send_interviewer_notification(interviewer_email: str, interviewer_name: str, candidate_name: str,
                                         job_title: str, interview_date: str, interview_time: str,
                                         meet_link: str | None = None, notes: str | None = None) -> bool:
    meet_section = f"<p>Meeting link: <a href='{meet_link}'>{meet_link}</a></p>" if meet_link else ""
    html = _base(f"""
        <p>Dear <strong>{interviewer_name}</strong>,</p>
        <p>You are assigned to interview <strong>{candidate_name}</strong> for <strong>{job_title}</strong>.</p>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:8px;padding:20px;margin:20px 0;">
          <p style="margin:0 0 8px;"><strong>Date:</strong> {interview_date}</p>
          <p style="margin:0;"><strong>Time:</strong> {interview_time}</p>
        </div>
        {meet_section}
        <p>Please submit your score via the FairHire AI portal after the interview.</p>""")
    return await _send_email(interviewer_email, f"Interview Assignment — {candidate_name} for {job_title}", html)
