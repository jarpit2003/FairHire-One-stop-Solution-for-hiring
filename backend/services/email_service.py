from __future__ import annotations

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings

log = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str) -> bool:
    if not settings.SMTP_ENABLED or not settings.SMTP_USERNAME:
        log.warning("[Email] SMTP not configured — skipping email to %s: %s", to, subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())
        log.info("[Email] Sent '%s' to %s", subject, to)
        return True
    except Exception as e:
        log.error("[Email] Failed to send to %s: %s", to, e)
        return False


def send_test_invite(to: str, candidate_name: str, job_title: str, test_link: str, deadline_hours: int = 48) -> bool:
    subject = f"FairHire AI — Technical Assessment for {job_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 22px;">FairHire AI</h1>
      </div>
      <div style="background: #f8fafc; padding: 32px; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
        <p style="color: #1e293b; font-size: 16px;">Hi <strong>{candidate_name}</strong>,</p>
        <p style="color: #475569;">You have been shortlisted for <strong>{job_title}</strong>. Please complete the assessment within <strong>{deadline_hours} hours</strong>.</p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{test_link}" style="background: #2563eb; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">Start Assessment →</a>
        </div>
        <p style="color: #94a3b8; font-size: 13px;">If the button doesn't work, copy this link: {test_link}</p>
      </div>
    </div>
    """
    return _send(to, subject, html)


def send_tech_interview_invite(to: str, candidate_name: str, job_title: str, scheduled_at: str, interviewer_name: str, meet_link: str = "") -> bool:
    subject = f"FairHire AI — Technical Interview Scheduled for {job_title}"
    meet_section = f'<p style="color: #475569;">Meeting link: <a href="{meet_link}">{meet_link}</a></p>' if meet_link else ""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 22px;">FairHire AI</h1>
      </div>
      <div style="background: #f8fafc; padding: 32px; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
        <p style="color: #1e293b;">Hi <strong>{candidate_name}</strong>,</p>
        <p style="color: #475569;">Your technical interview for <strong>{job_title}</strong> is scheduled.</p>
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
          <p style="margin: 0 0 8px 0;"><strong>Date &amp; Time:</strong> {scheduled_at}</p>
          <p style="margin: 0;"><strong>Interviewer:</strong> {interviewer_name}</p>
        </div>
        {meet_section}
      </div>
    </div>
    """
    return _send(to, subject, html)


def send_hr_interview_invite(to: str, candidate_name: str, job_title: str, scheduled_at: str, meet_link: str = "") -> bool:
    subject = f"FairHire AI — HR Interview Scheduled for {job_title}"
    meet_section = f'<p style="color: #475569;">Meeting link: <a href="{meet_link}">{meet_link}</a></p>' if meet_link else ""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 22px;">FairHire AI</h1>
      </div>
      <div style="background: #f8fafc; padding: 32px; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
        <p style="color: #1e293b;">Hi <strong>{candidate_name}</strong>,</p>
        <p style="color: #475569;">Your HR interview for <strong>{job_title}</strong> is scheduled for <strong>{scheduled_at}</strong>.</p>
        {meet_section}
      </div>
    </div>
    """
    return _send(to, subject, html)


def send_offer_letter(to: str, candidate_name: str, job_title: str, company_name: str = "FairHire AI", joining_date: str = "To be confirmed", ctc: str = "As discussed") -> bool:
    subject = f"Offer Letter — {job_title} at {company_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #059669; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0;">Congratulations!</h1>
      </div>
      <div style="background: #f8fafc; padding: 32px; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>We are delighted to offer you <strong>{job_title}</strong> at <strong>{company_name}</strong>.</p>
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
          <p style="margin: 0 0 8px 0;"><strong>Joining Date:</strong> {joining_date}</p>
          <p style="margin: 0;"><strong>CTC:</strong> {ctc}</p>
        </div>
        <p>Please reply to confirm acceptance within 3 business days.</p>
      </div>
    </div>
    """
    return _send(to, subject, html)


def send_rejection(to: str, candidate_name: str, job_title: str) -> bool:
    subject = f"FairHire AI — Update on your application for {job_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #64748b; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0;">FairHire AI</h1>
      </div>
      <div style="background: #f8fafc; padding: 32px; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Thank you for your interest in <strong>{job_title}</strong>. After careful consideration, we have decided to move forward with other candidates.</p>
        <p>We encourage you to apply for future openings. Best of luck in your career journey.</p>
      </div>
    </div>
    """
    return _send(to, subject, html)
