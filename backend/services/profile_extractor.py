"""
Rule-based candidate profile extractor.
Format-agnostic: works for student, experienced, academic, and international resumes.

Skill extraction   — four-tier section-aware pipeline
Education          — scoped to education section; field-of-study tokens safe inside slice only
Certifications     — vendor certs full-text + achievement section line extraction
Experience years   — explicit "N years" + date-range inference with future-year clamping
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from services.skill_taxonomy import SKILL_TAXONOMY

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CandidateProfile:
    skills: tuple[str, ...]
    education: tuple[str, ...]
    certifications: tuple[str, ...]
    experience_years: int | None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Shared heading prefix — horizontal whitespace + bullet chars only (no \n)
# ---------------------------------------------------------------------------

_H = r"[ \t\-#*\u2022\u2023\u25e6\u2043\u2219]*"


# ---------------------------------------------------------------------------
# Section heading patterns
# ---------------------------------------------------------------------------

_ANY_HEADING = re.compile(
    r"(?im)^[ \t]*(?:[A-Z][A-Za-z &/\-]{2,40})[ \t]*:?[ \t]*$"
)

_SKILL_HEADING = re.compile(
    rf"(?im)^{_H}"
    r"(?:technical\s+skills?|skills?|core\s+competenc(?:y|ies)"
    r"|tools?(?:\s+(?:&|and)\s+technologies?)?|technologies"
    r"|tech(?:nology)?\s+stack|key\s+skills?|areas?\s+of\s+expertise"
    r"|programming\s+languages?|languages?\s+(?:&|and)\s+frameworks?"
    r"|frameworks?(?:\s+(?:&|and)\s+libraries?)?|libraries?|platforms?)"
    rf"{_H}$"
)

_SKILL_STOP = re.compile(
    rf"(?im)^{_H}"
    r"(?:education|academic|experience|employment|work\s+history"
    r"|certifications?|courses?|awards?|publications?|volunteer"
    r"|languages?|references?|summary|objective"
    r"|projects?|personal\s+projects?|academic\s+projects?)"
    rf"{_H}$"
)

_PROJECT_HEADING = re.compile(
    rf"(?im)^{_H}"
    r"(?:projects?|personal\s+projects?|academic\s+projects?"
    r"|side\s+projects?|open[\s\-]source|portfolio"
    r"|notable\s+projects?|selected\s+projects?)"
    rf"{_H}$"
)

_PROJECT_STOP = re.compile(
    rf"(?im)^{_H}"
    r"(?:education|academic|experience|employment|work\s+history"
    r"|certifications?|courses?|awards?|publications?"
    r"|volunteer|languages?|references?|summary|objective)"
    rf"{_H}$"
)

_EXP_HEADING = re.compile(
    rf"(?im)^{_H}"
    r"(?:work\s+experience|professional\s+experience|employment\s+history"
    r"|employment|experience|internships?|work\s+history)"
    rf"{_H}$"
)

_EXP_STOP = re.compile(
    rf"(?im)^{_H}"
    r"(?:education|academic|certifications?|courses?|awards?"
    r"|publications?|projects?|volunteer|languages?"
    r"|references?|skills?|summary|objective)"
    rf"{_H}$"
)

_EDU_HEADING = re.compile(
    rf"(?im)^{_H}"
    r"(?:education|academic(?:\s+background)?|qualifications?"
    r"|academic\s+qualifications?)"
    rf"{_H}$"
)

_ACHIEVEMENT_HEADING = re.compile(
    rf"(?im)^{_H}"
    r"(?:achievements?\s+and\s+certifications?"
    r"|certifications?\s+and\s+achievements?"
    r"|achievements?|certifications?|awards?\s+and\s+certifications?"
    r"|honours?|honors?|recognitions?|accomplishments?)"
    rf"{_H}$"
)

_TECH_STACK_LINE = re.compile(
    r"(?i)(?:tech(?:nologies)?(?:\s+used)?|built\s+with"
    r"|stack|tools?|frameworks?|languages?)\s*[:\-]"
)


# ---------------------------------------------------------------------------
# Skill patterns (compiled once at import)
# ---------------------------------------------------------------------------

_SKILL_PATTERNS: dict[str, re.Pattern[str]] = {
    canonical: re.compile(r"(?i)(?:" + "|".join(aliases) + r")")
    for canonical, aliases in SKILL_TAXONOMY.items()
}


# ---------------------------------------------------------------------------
# Education patterns
# ---------------------------------------------------------------------------

_DEGREE_PATTERN = re.compile(
    r"(?i)\b("
    r"b\.?\s*tech\.?(?:\s+in\s+[\w\s]+)?"
    r"|b\.?\s*e\.?(?:\s+in\s+[\w\s]+)?"
    r"|bachelor\s+of\s+engineering(?:\s+in\s+[\w\s]+)?"
    r"|bachelor\s+of\s+technology(?:\s+in\s+[\w\s]+)?"
    r"|bachelor(?:'?s)?(?:\s+of\s+[\w\s]+)?"
    r"|master(?:'?s)?(?:\s+of\s+[\w\s]+)?"
    r"|ph\.?d\.?(?:\s+in\s+[\w\s]+)?"
    r"|b\.?s\.?c?\.?"
    r"|m\.?s\.?c?\.?"
    r"|m\.?b\.?a\.?"
    r"|associate(?:'?s)?(?:\s+of\s+[\w\s]+)?"
    r"|high\s+school\s+diploma"
    r"|diploma"
    r")\b"
)

# Only applied inside an education section slice — prevents false positives
# from Skills / Projects sections on any resume format.
_FIELD_PATTERN = re.compile(
    r"(?i)\b("
    r"computer\s+science"
    r"|information\s+technology"
    r"|computer\s+engineering"
    r"|software\s+engineering"
    r"|electrical\s+engineering"
    r"|mechanical\s+engineering"
    r"|civil\s+engineering"
    r"|data\s+science"
    r"|artificial\s+intelligence"
    r"|machine\s+learning"
    r"|mathematics|physics|economics"
    r"|business\s+administration"
    r")\b"
)


# ---------------------------------------------------------------------------
# Certification patterns
# ---------------------------------------------------------------------------

# Vendor / professional certs — matched anywhere (unambiguous by name)
_CERT_PATTERN = re.compile(
    r"(?i)\b("
    r"aws\s+certified[\w\s\-]*"
    r"|google\s+cloud\s+certified[\w\s\-]*"
    r"|azure\s+certified[\w\s\-]*"
    r"|certified\s+kubernetes[\w\s\-]*"
    r"|ckad|cka|cks"
    r"|pmp|cpa|cissp"
    r"|comptia[\w\s\+]*"
    r"|oracle\s+certified[\w\s\-]*"
    r"|tensorflow\s+developer\s+certificate"
    r"|professional\s+scrum[\w\s\-]*"
    r"|certified\s+scrum[\w\s\-]*"
    r"|udemy[\w\s\-]*(?:certificate|course|bootcamp)"
    r"|coursera[\w\s\-]*(?:certificate|specialization)?"
    r"|nptel[\w\s\-]*"
    r"|certificate\s+(?:of\s+)?(?:completion|achievement|excellence)[\w\s\-]*"
    r")\b"
)

# Signal words that mark an achievement-section line as worth extracting
_ACHIEVEMENT_SIGNAL = re.compile(
    r"(?i)(?:awarded|winner|won|finalist|semi.?finalist|pre.?final"
    r"|ranked|rank\s+\d|certificate|certified|scholarship"
    r"|selected\s+for|selected\s+as|published|publication|patent)"
)


# ---------------------------------------------------------------------------
# Experience patterns
# ---------------------------------------------------------------------------

_EXP_EXPLICIT = re.compile(
    r"(?i)(\d+)\+?\s+years?\s+(?:of\s+)?(?:professional\s+)?experience"
)

_MONTHS = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?"
    r"|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_DATE_RANGE = re.compile(
    rf"(?i)(?:{_MONTHS}\s+)?(\d{{4}})"
    rf"\s*[\u2013\u2014\-]{{1,2}}\s*"
    rf"(?:(?:{_MONTHS}\s+)?(\d{{4}})|present|current|now|till\s+date|to\s+date)"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_profile(text: str, raw_text: str = "") -> CandidateProfile:
    """
    text     — cleaned text, used for skills/education/certs/experience
    raw_text — uncleaned text, used for email/phone/name (avoids cleanup corruption)
    """
    contact_src = raw_text if raw_text.strip() else text
    name  = _extract_name(contact_src)
    email = _extract_email(contact_src)
    phone = _extract_phone(contact_src)

    # Upgrade 5 — structured log for debugging extraction quality
    confidence = contact_confidence(email, phone, name)
    log.info(
        "[extract_profile] name=%r email=%r phone=%r confidence=%d",
        name, email, phone, confidence
    )
    if confidence < 50:
        log.warning("[extract_profile] low contact confidence (%d) — check raw text quality", confidence)

    return CandidateProfile(
        skills=_extract_skills(text),
        education=_extract_education(text),
        certifications=_extract_certifications(text),
        experience_years=_extract_experience_years(text),
        full_name=name,
        email=email,
        phone=phone,
        raw_text=text,
    )


# ---------------------------------------------------------------------------
# Skill extraction — four-tier pipeline
# ---------------------------------------------------------------------------

def _extract_skills(text: str) -> tuple[str, ...]:
    seen:   set[str]  = set()
    result: list[str] = []

    def _collect(src: str, tier: str) -> None:
        before = len(result)
        for canonical, pat in _SKILL_PATTERNS.items():
            if canonical not in seen and pat.search(src):
                seen.add(canonical)
                result.append(canonical)
        added = result[before:]
        log.debug("[skills][%s] added=%s", tier, added) if added else \
            log.debug("[skills][%s] none", tier)

    for i, block in enumerate(_slice_all(_SKILL_HEADING, _SKILL_STOP, text)):
        log.debug("[skills][tier1][block%d] preview=%r", i, block[:120])
        _collect(block, f"tier1/b{i}")

    for i, block in enumerate(_slice_all(_PROJECT_HEADING, _PROJECT_STOP, text)):
        focused = _tech_stack_lines(block)
        _collect(focused if focused.strip() else block, f"tier2/b{i}")

    exp = _slice_one(_EXP_HEADING, _EXP_STOP, text)
    if exp:
        _collect(exp, "tier3")

    _collect(text, "tier4/fallback")
    log.debug("[skills][final] %d skills", len(result))
    return tuple(result)


# ---------------------------------------------------------------------------
# Education extraction — section-scoped
# ---------------------------------------------------------------------------

def _extract_education(text: str) -> tuple[str, ...]:
    edu = _slice_section(text, _EDU_HEADING)
    scan = edu if edu.strip() else text
    use_fields = bool(edu.strip())

    seen:   set[str]  = set()
    unique: list[str] = []

    for m in _DEGREE_PATTERN.findall(scan):
        n = " ".join(m.split()).title()
        if n not in seen:
            seen.add(n)
            unique.append(n)

    if use_fields:
        for m in _FIELD_PATTERN.findall(edu):
            n = " ".join(m.split()).title()
            if n not in seen:
                seen.add(n)
                unique.append(n)

    return tuple(unique)


# ---------------------------------------------------------------------------
# Certification extraction — vendor certs + achievement section lines
# ---------------------------------------------------------------------------

def _extract_certifications(text: str) -> tuple[str, ...]:
    seen:   set[str]  = set()
    unique: list[str] = []

    for m in _CERT_PATTERN.findall(text):
        n = " ".join(m.split()).title()
        if n not in seen:
            seen.add(n)
            unique.append(n)

    ach = _slice_section(text, _ACHIEVEMENT_HEADING)
    if ach.strip():
        for line in ach.splitlines():
            line = line.strip().lstrip("-\u2022\u00b7* ")
            if len(line) < 8:
                continue
            if _ACHIEVEMENT_SIGNAL.search(line):
                entry = " ".join(line.split())[:80].rstrip(",.:").title()
                if entry not in seen:
                    seen.add(entry)
                    unique.append(entry)

    return tuple(unique)


# ---------------------------------------------------------------------------
# Experience years extraction
# ---------------------------------------------------------------------------

def _extract_experience_years(text: str) -> int | None:
    hits: list[int] = [int(n) for n in _EXP_EXPLICIT.findall(text)]

    scoped = _slice_one(_EXP_HEADING, _EXP_STOP, text)
    search = scoped if scoped.strip() else text

    cy = _current_year()
    for m in _DATE_RANGE.finditer(search):
        try:
            start = min(int(m.group(1)), cy)
            end   = min(int(m.group(2)) if m.group(2) else cy, cy)
            span  = end - start
            hits.append(span if span > 0 else 1)
        except (TypeError, ValueError):
            continue

    # Filter out unreasonably large spans (education dates etc.)
    hits = [h for h in hits if 0 < h <= 50]
    return max(hits) if hits else None


# ---------------------------------------------------------------------------
# Section slicing helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return (text.replace("\r\n", "\n").replace("\r", "\n")
                .replace("\u2028", "\n").replace("\u2029", "\n"))


def _slice_all(
    heading: re.Pattern[str],
    stop: re.Pattern[str],
    text: str,
) -> list[str]:
    """Return all non-empty blocks under every matching heading."""
    text = _normalise(text)
    slices: list[str] = []
    pos = 0
    while True:
        hm = heading.search(text, pos)
        if not hm:
            break
        start = hm.end()
        sm = stop.search(text, start)
        end = sm.start() if sm else len(text)
        pos = sm.end() if sm else len(text)
        block = text[start:end].strip()
        if block:
            slices.append(block)
    return slices


def _slice_one(
    heading: re.Pattern[str],
    stop: re.Pattern[str],
    text: str,
) -> str:
    """Return the first block under a matching heading."""
    blocks = _slice_all(heading, stop, text)
    return blocks[0] if blocks else ""


def _slice_section(text: str, heading: re.Pattern[str]) -> str:
    """Return text under the first matching heading until the next heading."""
    text = _normalise(text)
    m = heading.search(text)
    if not m:
        return ""
    start = m.end()
    stop  = _ANY_HEADING.search(text, start)
    end   = stop.start() if stop else len(text)
    return text[start:end].strip()


def _tech_stack_lines(block: str) -> str:
    """Extract lines following a tech-stack signal inside a project block."""
    lines = block.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if _TECH_STACK_LINE.search(line):
            capturing = True
            parts = re.split(r"[:\-]", line, maxsplit=1)
            if len(parts) > 1:
                out.append(parts[1])
            continue
        if capturing:
            if not line.strip() or _ANY_HEADING.match(line):
                capturing = False
            else:
                out.append(line)
    return "\n".join(out)


def _current_year() -> int:
    from datetime import date
    return date.today().year


# ---------------------------------------------------------------------------
# Contact extraction
# ---------------------------------------------------------------------------

# Email regex — matches standard emails, tolerates being preceded by
# spaces/separators that remain after symbol stripping
_EMAIL_RE = re.compile(
    r"(?<![a-zA-Z0-9])"     # not preceded by alphanumeric (prevents partial matches)
    r"([a-zA-Z0-9][a-zA-Z0-9._%+\-]{0,63}"  # local part
    r"@"
    r"[a-zA-Z0-9][a-zA-Z0-9.\-]{0,253}"     # domain
    r"\.[a-zA-Z]{2,})"      # TLD
    r"(?![a-zA-Z0-9@])"     # not followed by alphanumeric or another @
)

# Known fake/placeholder domains to reject
_FAKE_DOMAINS = {"example.com", "test.com", "email.com", "domain.com", "fairhire.local", "quantumlogic.local", "mail.com"}

# Phone — requires 10+ digits, anchored to avoid matching inside longer numbers
_PHONE_RE = re.compile(
    r"(?<![\d])"                          # not preceded by digit
    r"(\+?\d[\d\s\-().]{8,18}\d)"         # 10-20 char phone string
    r"(?![\d])"                           # not followed by digit
)

_HEADING_WORDS_SET = {
    "summary", "objective", "profile", "skills", "experience", "education",
    "certifications", "projects", "contact", "references", "awards",
    "publications", "volunteer", "languages", "resume", "curriculum", "vitae",
    "declaration", "hobbies", "interests", "achievements",
    # multi-word headings that appear as ALL-CAPS in PDFs
    "relevant coursework", "coursework", "technical skills", "work experience",
    "professional experience", "personal projects", "academic projects",
    "key skills", "core competencies", "employment history", "career objective",
    "professional summary", "areas of expertise", "tools and technologies",
}

# Contact section signal — lines containing these are likely in the header
_CONTACT_SIGNAL = re.compile(
    r"(?i)(email|phone|mobile|contact|linkedin|github|portfolio|address|tel)"
)


def _contact_zone(text: str) -> str:
    lines = text.splitlines()
    zone_lines = lines[:25]
    for line in lines[25:60]:
        if _CONTACT_SIGNAL.search(line):
            zone_lines.append(line)
    return "\n".join(zone_lines)


def _normalize_contact_text(text: str) -> str:
    """
    Normalize contact zone text:
    - Strip emoji/symbol prefixes before emails and phones
    - Fix spaced @ and dots
    - Handle [at] / (at) obfuscation
    - Normalize brackets/pipes around emails
    - Add https:// to bare links
    """
    # Strip common emoji/unicode symbols used as contact icons
    # Covers: ✉✉️📧📨📱📞☎️☏📍🔗👤👥•‣◦⁃∙·–—|│
    text = re.sub(
        r"[\u2709\u2709\U0001f4e7\U0001f4e8\U0001f4f1\U0001f4de"
        r"\u260e\u260f\U0001f4cd\U0001f517\U0001f464\U0001f465"
        r"\u2022\u2023\u25e6\u2043\u2219\u00b7\u2013\u2014"
        r"\u2502\u2503|\*#>]+\s*",
        " ", text
    )

    # Remove brackets/parens wrapping emails: [email] (email)
    text = re.sub(r"[\[\(]([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\]\)]", r"\1", text)

    # Fix spaced @: deep @ gmail.com or deep @gmail.com
    text = re.sub(r"([a-zA-Z0-9._%+\-])\s+@\s*([a-zA-Z0-9])", r"\1@\2", text)
    text = re.sub(r"([a-zA-Z0-9._%+\-])@\s+([a-zA-Z0-9])", r"\1@\2", text)

    # Fix spaced dots in domain: gmail . com -> gmail.com
    text = re.sub(r"([a-zA-Z0-9])\s\.\s([a-zA-Z]{2,6})(?=\s|$|[|,;])", r"\1.\2", text)

    # Fix [at] / (at) / {at} obfuscation
    text = re.sub(r"\s*[\[\(\{]\s*at\s*[\]\)\}]\s*", "@", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*", ".", text, flags=re.IGNORECASE)

    # Add https:// to bare linkedin/github links so link_verifier picks them up
    text = re.sub(r"(?<![/\w])(linkedin\.com/[\w/\-]+)", r"https://\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<![/\w])(github\.com/[\w/\-]+)", r"https://\1", text, flags=re.IGNORECASE)

    # Remove zero-width and non-breaking spaces
    text = text.replace("\u200b", "").replace("\u00a0", " ").replace("\ufeff", "")

    return text


def _extract_email(text: str) -> str | None:
    """
    Multi-pass email extraction:
    1. Contact zone (first 25 lines) — normalized
    2. Full text — normalized
    3. Aggressive scan for any @-containing token
    Prefers personal domains over edu/college domains.
    """
    def _scan(src: str) -> list[str]:
        normalized = _normalize_contact_text(src)
        found: list[str] = []
        for m in _EMAIL_RE.finditer(normalized):
            email = m.group(1).lower().strip(".")
            local = email.split("@")[0]
            if local.endswith(".") or local.startswith("."):
                continue
            domain = email.split("@")[1] if "@" in email else ""
            if domain in _FAKE_DOMAINS:
                continue
            # Reject emails inside URLs
            pos = m.start()
            preceding = normalized[max(0, pos - 15):pos]
            if "://" in preceding or preceding.rstrip().endswith("/"):
                continue
            found.append(email)
        return found

    def _prefer(candidates: list[str]) -> str | None:
        if not candidates:
            return None
        # Prefer personal domains over edu/college domains
        # but ALWAYS return something — never discard a valid edu email
        personal = [e for e in candidates if not any(
            e.split("@")[1].endswith(s) for s in (".edu", ".ac.in", ".edu.in", ".ac.uk", ".edu.au")
        )]
        return (personal or candidates)[0]

    # Pass 1: contact zone
    result = _prefer(_scan(_contact_zone(text)))
    if result:
        return result

    # Pass 2: full text
    result = _prefer(_scan(text))
    if result:
        return result

    # Pass 3: aggressive — look for anything with @ in first 60 lines
    for line in text.splitlines()[:60]:
        line = _normalize_contact_text(line)
        # Find token containing @
        for token in line.split():
            token = token.strip("<>()[]|,;")
            if "@" in token and "." in token.split("@")[-1]:
                email = token.lower().strip(".")
                if re.match(r"[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email):
                    return email

    return None


def _extract_phone(text: str) -> str | None:
    """Extract phone — strips emoji/symbol prefixes, normalizes, fallback from contact zone to full text."""
    for search_text in [_contact_zone(text), text]:
        normalized = _normalize_contact_text(search_text)
        for m in _PHONE_RE.finditer(normalized):
            raw = m.group(1).strip()
            digits = sum(c.isdigit() for c in raw)
            if digits < 10 or digits > 15:
                continue
            # Reject 8-digit year-like patterns
            if re.fullmatch(r"\d{4}[\s\-]\d{4}", raw.strip()):
                continue
            return raw
    return None


def contact_confidence(email: str | None, phone: str | None, name: str | None) -> int:
    """Upgrade 4 — confidence score for contact extraction quality."""
    score = 0
    if email:
        score += 40
        # bonus for common personal domains
        domain = email.split("@")[1] if "@" in email else ""
        if any(domain.endswith(d) for d in ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com")):
            score += 10
    if phone:
        score += 40
    if name:
        score += 10
    return min(score, 100)


def _extract_name(text: str) -> str | None:
    """
    Extract candidate name — scans first 15 lines.
    Handles: normal case, ALL CAPS, hyphenated names.
    If a line has both name and email, extracts just the name part.
    Fallback: derives name from email local part if no standalone name found.
    """
    lines = text.splitlines()[:15]
    first_email = None

    for line in lines:
        line = line.strip()
        if not line or len(line) > 120:
            continue

        # Strip leading emoji/symbols/bullets that PDFs often put before names
        line = re.sub(
            r"^[\u2022\u2023\u25e6\u2043\u2219\u00b7\u2013\u2014\u2709"
            r"\U0001f4e7\U0001f4f1\U0001f4de\u260e\u260f\U0001f464"
            r"|\*#>\-=~]+\s*",
            "", line
        ).strip()

        # If line contains an email, strip everything from @ onwards and try the remainder
        if "@" in line:
            # Capture the email for fallback
            if not first_email:
                m = _EMAIL_RE.search(line)
                if m:
                    first_email = m.group(1)
            # Take only the part before the email address
            email_pos = line.index("@")
            start = email_pos
            while start > 0 and line[start - 1] not in (" ", "\t", "|", ","):
                start -= 1
            line = line[:start].strip()
            if not line:
                continue

        # Skip lines with URLs or phone numbers
        if "http" in line or "/" in line:
            continue
        if _PHONE_RE.search(line):
            continue

        words = line.split()
        if len(words) < 2 or len(words) > 5:
            continue
        if any(c.isdigit() for c in line):
            continue
        if any(c in line for c in "|\\<>{}[]#$%"):
            continue
        if line.lower().rstrip(":") in _HEADING_WORDS_SET:
            continue

        # ALL CAPS names
        if line.isupper():
            if all(w.replace("-", "").isalpha() for w in words):
                candidate = line.title()
                if " ".join(words).lower() not in _HEADING_WORDS_SET:
                    return candidate
            continue

        # Normal / title case
        clean = [w.replace("-", "").replace("'", "") for w in words]
        if all(w and w[0].isupper() and w.isalpha() for w in clean):
            return line

    # Fallback: derive name from email local part if no standalone name found
    if first_email:
        local = first_email.split("@")[0]
        # Remove numbers and special chars, split on dots/underscores
        parts = re.split(r"[._\-\d]+", local)
        name_parts = [p.capitalize() for p in parts if p and len(p) > 1]
        if len(name_parts) >= 2:
            return " ".join(name_parts[:3])

    return None
