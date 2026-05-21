"""
services/publisher_service.py

Publishes a job to external platforms.

Platform status:
  linkedin  — generates a pre-filled share URL (no API approval needed)
  naukri    — generates a copy-ready formatted post (no API needed)
  x         — posts via X API v2 (needs API keys in config)
  google_form — creates a Google Form (needs credentials.json — stub until then)
"""
from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass

from config import settings

log = logging.getLogger(__name__)


@dataclass
class PublishResult:
    platform: str
    success: bool
    url: str | None       # shareable URL or post URL
    message: str


# ---------------------------------------------------------------------------
# LinkedIn — pre-filled share URL (no API key needed)
# ---------------------------------------------------------------------------

def publish_linkedin(title: str, description: str, form_url: str | None) -> PublishResult:
    """
    Generates a LinkedIn share URL. HR clicks it → LinkedIn opens with
    the job post pre-filled. No API approval needed.
    """
    summary = (description or "")[:700].strip()
    apply_line = f"\n\nApply here: {form_url}" if form_url else ""
    text = f"{title}\n\n{summary}{apply_line}"
    params = urllib.parse.urlencode({"mini": "true", "title": title, "summary": text})
    url = f"https://www.linkedin.com/shareArticle?{params}"
    return PublishResult(
        platform="linkedin",
        success=True,
        url=url,
        message="LinkedIn share URL generated. Click to post.",
    )


# ---------------------------------------------------------------------------
# Naukri — formatted copy-ready post
# ---------------------------------------------------------------------------

def publish_naukri(title: str, description: str, form_url: str | None) -> PublishResult:
    """
    Generates a Naukri-formatted job post text.
    HR copies it into Naukri's job posting form.
    """
    apply_line = f"\n\nApply Link: {form_url}" if form_url else ""
    post = (
        f"Job Title: {title}\n\n"
        f"{(description or '').strip()}"
        f"{apply_line}\n\n"
        f"--- Posted via FairHire AI ---"
    )
    return PublishResult(
        platform="naukri",
        success=True,
        url=None,
        message=post,
    )


# ---------------------------------------------------------------------------
# X (Twitter) — post via API v2
# ---------------------------------------------------------------------------

async def publish_x(title: str, description: str, form_url: str | None) -> PublishResult:
    """
    Posts a job tweet via X API v2.
    Requires X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET in config.
    Falls back gracefully if keys not set.
    """
    if not settings.X_ENABLED:
        snippet = (description or "")[:120].strip()
        apply_line = f" Apply: {form_url}" if form_url else ""
        tweet = f"We're hiring! {title}\n\n{snippet}...{apply_line} #hiring #jobs"
        return PublishResult(
            platform="x",
            success=False,
            url=None,
            message=f"X posting disabled. Set X_ENABLED=true in .env. Draft tweet:\n\n{tweet}",
        )

    try:
        import httpx, hmac, hashlib, base64, time, uuid as _uuid

        snippet   = (description or "")[:200].strip()
        apply_line = f" Apply: {form_url}" if form_url else ""
        tweet_text = f"We're hiring! {title}\n\n{snippet}...{apply_line} #hiring #jobs"
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        # OAuth 1.0a signature
        url    = "https://api.twitter.com/2/tweets"
        method = "POST"
        ts     = str(int(time.time()))
        nonce  = _uuid.uuid4().hex

        oauth_params = {
            "oauth_consumer_key":     settings.X_API_KEY,
            "oauth_nonce":            nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp":        ts,
            "oauth_token":            settings.X_ACCESS_TOKEN,
            "oauth_version":          "1.0",
        }

        param_str = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
            for k, v in sorted(oauth_params.items())
        )
        base_str = "&".join([
            method,
            urllib.parse.quote(url, safe=""),
            urllib.parse.quote(param_str, safe=""),
        ])
        signing_key = (
            urllib.parse.quote(settings.X_API_SECRET, safe="") + "&" +
            urllib.parse.quote(settings.X_ACCESS_TOKEN_SECRET, safe="")
        )
        sig = base64.b64encode(
            hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()
        ).decode()
        oauth_params["oauth_signature"] = sig

        auth_header = "OAuth " + ", ".join(
            f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
            for k, v in sorted(oauth_params.items())
        )

        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.post(
                url,
                json={"text": tweet_text},
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
            )

        if resp.status_code in (200, 201):
            data    = resp.json()
            tweet_id = data.get("data", {}).get("id", "")
            tweet_url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None
            return PublishResult(platform="x", success=True, url=tweet_url,
                                 message="Tweet posted successfully.")
        else:
            return PublishResult(platform="x", success=False, url=None,
                                 message=f"X API error {resp.status_code}: {resp.text[:200]}")

    except Exception as exc:
        log.warning("publish_x failed: %s", exc)
        return PublishResult(platform="x", success=False, url=None, message=str(exc))


# ---------------------------------------------------------------------------
# Google Forms — stub (activate when credentials.json provided)
# ---------------------------------------------------------------------------

async def create_google_form(job_id: str, title: str, description: str) -> PublishResult:
    """
    Creates a Google Form for job applications with all required fields.
    Requires credentials.json (Google service account) and GOOGLE_FORMS_ENABLED=true.
    """
    if not settings.GOOGLE_FORMS_ENABLED:
        return PublishResult(
            platform="google_form",
            success=False,
            url=None,
            message=(
                "Google Forms not configured. "
                "Add credentials.json and set GOOGLE_FORMS_ENABLED=true in .env to activate."
            ),
        )

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _create_form_sync, job_id, title, description)
        return result
    except Exception as exc:
        log.error("create_google_form failed: %s", exc)
        return PublishResult(platform="google_form", success=False, url=None, message=str(exc))


def _create_form_sync(job_id: str, title: str, description: str) -> PublishResult:
    """Synchronous Google Forms creation — runs in executor."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_CREDENTIALS_PATH,
        scopes=[
            "https://www.googleapis.com/auth/forms.body",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    forms_service = build("forms", "v1", credentials=creds)

    # Step 1: Create the form shell
    form_body = {
        "info": {
            "title": f"Apply: {title}",
            "documentTitle": f"FairHire Application — {title}",
        }
    }
    form = forms_service.forms().create(body=form_body).execute()
    form_id = form["formId"]

    # Step 2: Add all fields in one batchUpdate
    # Field titles must match what google_form_webhook.gs expects
    requests = [
        _text_question(0, "Full Name", required=True),
        _text_question(1, "Email Address", required=True),
        _text_question(2, "Phone Number", required=False),
        _text_question(3, "LinkedIn URL", required=False),
        _paragraph_question(4, "Resume Text",
            description="Paste your full resume / CV text here.",
            required=True),
        _paragraph_question(5, "Cover Note",
            description="Why are you interested in this role? (optional)",
            required=False),
    ]

    forms_service.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests},
    ).execute()

    # Step 3: Make the form publicly accessible via Drive
    drive_service = build("drive", "v3", credentials=creds)
    drive_service.permissions().create(
        fileId=form_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    form_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
    log.info("Google Form created: %s", form_url)

    return PublishResult(
        platform="google_form",
        success=True,
        url=form_url,
        message=(
            f"Form created. URL: {form_url}\n\n"
            f"Next step: open the form → Script editor → paste google_form_webhook.gs → "
            f"set JOB_ID='{job_id}' → add onFormSubmit trigger."
        ),
    )


def _text_question(index: int, title: str, required: bool) -> dict:
    return {
        "createItem": {
            "item": {
                "title": title,
                "questionItem": {
                    "question": {
                        "required": required,
                        "textQuestion": {"paragraph": False},
                    }
                },
            },
            "location": {"index": index},
        }
    }


def _paragraph_question(index: int, title: str, description: str, required: bool) -> dict:
    return {
        "createItem": {
            "item": {
                "title": title,
                "description": description,
                "questionItem": {
                    "question": {
                        "required": required,
                        "textQuestion": {"paragraph": True},
                    }
                },
            },
            "location": {"index": index},
        }
    }
