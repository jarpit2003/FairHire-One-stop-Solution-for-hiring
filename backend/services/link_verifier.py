"""
services/link_verifier.py

Extracts all URLs from resume text and verifies each one:
  - Any URL   : HTTP HEAD request — checks the link resolves (status < 400)
  - GitHub    : public API — confirms repo/profile exists + checks commit activity
  - LinkedIn  : HTTP HEAD only (no scraping — just confirms URL resolves)

Returns a list of LinkResult objects. Falls back gracefully on network errors.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_URL_RE = re.compile(
    r"https?://[^\s\"'<>(){}\[\]\\,;]+"
)

_GITHUB_REPO_RE  = re.compile(r"github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?$")
_GITHUB_USER_RE  = re.compile(r"github\.com/([^/\s]+)/?$")
_LINKEDIN_RE     = re.compile(r"linkedin\.com/in/([^/\s]+)")

_TIMEOUT = httpx.Timeout(8.0)
_HEADERS = {"User-Agent": "FairHire-LinkVerifier/1.0"}


@dataclass
class LinkResult:
    url: str
    reachable: bool
    platform: str           # "github_repo" | "github_profile" | "linkedin" | "web"
    detail: str             # human-readable status for HR UI
    commit_activity: bool   # True if GitHub repo has recent commits (last 90 days)


async def verify_links(resume_text: str) -> list[LinkResult]:
    """Extract all URLs from resume_text and verify each concurrently."""
    urls = _extract_urls(resume_text)
    if not urls:
        return []
    async with httpx.AsyncClient(
        timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True, verify=False
    ) as client:
        tasks = [_verify_one(client, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    out: list[LinkResult] = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            out.append(LinkResult(url=url, reachable=False, platform="web",
                                  detail=f"Error: {result}", commit_activity=False))
        else:
            out.append(result)
    return out


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _extract_urls(text: str) -> list[str]:
    raw = _URL_RE.findall(text)
    # Deduplicate preserving order, strip trailing punctuation artifacts
    seen: set[str] = set()
    clean: list[str] = []
    for u in raw:
        u = u.rstrip(".,;:!?)")
        if u not in seen:
            seen.add(u)
            clean.append(u)
    return clean


async def _verify_one(client: httpx.AsyncClient, url: str) -> LinkResult:
    # GitHub repo  e.g. github.com/user/repo
    m = _GITHUB_REPO_RE.search(url)
    if m:
        return await _check_github_repo(client, url, m.group(1), m.group(2))

    # GitHub profile  e.g. github.com/user
    m = _GITHUB_USER_RE.search(url)
    if m:
        return await _check_github_profile(client, url, m.group(1))

    # LinkedIn
    if _LINKEDIN_RE.search(url):
        return await _check_generic(client, url, platform="linkedin")

    # Generic web
    return await _check_generic(client, url, platform="web")


async def _check_github_repo(
    client: httpx.AsyncClient, url: str, owner: str, repo: str
) -> LinkResult:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        r = await client.get(api, headers={**_HEADERS, "Accept": "application/vnd.github+json"})
        if r.status_code == 404:
            return LinkResult(url=url, reachable=False, platform="github_repo",
                              detail="Repository not found", commit_activity=False)
        if r.status_code != 200:
            return LinkResult(url=url, reachable=False, platform="github_repo",
                              detail=f"GitHub API {r.status_code}", commit_activity=False)

        data = r.json()
        stars    = data.get("stargazers_count", 0)
        forks    = data.get("forks_count", 0)
        pushed   = data.get("pushed_at", "")

        # Check commit activity in last 90 days
        active = False
        if pushed:
            from datetime import datetime, timezone, timedelta
            try:
                last_push = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                active = (datetime.now(timezone.utc) - last_push) < timedelta(days=90)
            except ValueError:
                pass

        detail = f"{stars} stars, {forks} forks, last push: {pushed[:10]}"
        return LinkResult(url=url, reachable=True, platform="github_repo",
                          detail=detail, commit_activity=active)
    except Exception as exc:
        log.debug("github_repo check failed %s: %s", url, exc)
        return LinkResult(url=url, reachable=False, platform="github_repo",
                          detail=str(exc), commit_activity=False)


async def _check_github_profile(
    client: httpx.AsyncClient, url: str, username: str
) -> LinkResult:
    api = f"https://api.github.com/users/{username}"
    try:
        r = await client.get(api, headers={**_HEADERS, "Accept": "application/vnd.github+json"})
        if r.status_code == 404:
            return LinkResult(url=url, reachable=False, platform="github_profile",
                              detail="GitHub user not found", commit_activity=False)
        if r.status_code != 200:
            return LinkResult(url=url, reachable=False, platform="github_profile",
                              detail=f"GitHub API {r.status_code}", commit_activity=False)

        data   = r.json()
        repos  = data.get("public_repos", 0)
        detail = f"{repos} public repos"
        return LinkResult(url=url, reachable=True, platform="github_profile",
                          detail=detail, commit_activity=repos > 0)
    except Exception as exc:
        log.debug("github_profile check failed %s: %s", url, exc)
        return LinkResult(url=url, reachable=False, platform="github_profile",
                          detail=str(exc), commit_activity=False)


async def _check_generic(
    client: httpx.AsyncClient, url: str, platform: str
) -> LinkResult:
    try:
        r = await client.head(url)
        reachable = r.status_code < 400
        detail    = f"HTTP {r.status_code}"
        # Some servers reject HEAD — retry with GET if 405
        if r.status_code == 405:
            r2 = await client.get(url)
            reachable = r2.status_code < 400
            detail    = f"HTTP {r2.status_code}"
        return LinkResult(url=url, reachable=reachable, platform=platform,
                          detail=detail, commit_activity=False)
    except Exception as exc:
        log.debug("generic check failed %s: %s", url, exc)
        return LinkResult(url=url, reachable=False, platform=platform,
                          detail=str(exc), commit_activity=False)
