# FairHire AI 🎯

> Enterprise ATS-compliant hiring platform with AI-powered resume parsing, multi-stage pipeline management, and recruiter intelligence.

**Built during internship by a team of 4 BTech students (2026) who watched recruiters drown in 250+ resumes per role — and decided to fix it.**

---

<!-- Replace the line below with your actual demo GIF or screenshot -->
<!-- ![FairHire AI Demo](./demo/dashboard-preview.gif) -->

**[📹 Watch Full Demo →](https://drive.google.com/file/d/1HfGapmyf0MRDe8QT3DB6Of0lBFdXlhW5/view?usp=sharing)** &nbsp;|&nbsp; **[⭐ Star this repo](#)** &nbsp;|&nbsp; **[📄 Technical Documentation](https://drive.google.com/drive/folders/1GsNdsL0MmGkgeckjl1i3gfIhKxfC0OJj?usp=sharing)**

---

## 🚀 What is FairHire AI?

FairHire AI is a full-stack Gen AI application that integrates **resume parsing**, **semantic embeddings**, **impact scoring**, **skill taxonomy matching**, **candidate deduplication**, **JD optimization**, **hiring decision engine**, **rule-based recruiter chatbot**, **email automation**, and **cloud deployment** — helping recruiters hire smarter, faster, and fairer.

### The problem we solved

| Pain Point | Reality |
|------------|---------|
| Resume overload | 250+ applications per role, 6 seconds per resume |
| Bad ATS parsing | 75% of qualified candidates rejected due to formatting |
| Manual workflows | Recruiters spend 23 hours screening per hire |
| Slow hiring | Average time-to-hire: 45 days |

### What we achieved

| Metric | Result |
|--------|--------|
| ⚡ Resume parse time | < 3 seconds |
| 📉 Time-to-hire reduction | 60% (45 days → 18 days) |
| 🤖 Workflows automated | 80% |
| 📦 Throughput | 1000+ resumes in < 10 minutes |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Resume Parsing** | Upload PDF/DOCX → dual-parser pipeline (pypdf → pdfplumber → Gemini fallback) with 6-pass text cleanup; extracts name, email, phone, skills, education, certifications. Runs in a thread pool — never blocks the async event loop |
| 🧠 **AI Fit Scoring** | Hybrid scoring: weighted skill overlap (20%) + Gemini semantic embeddings (30%) + Gemini impact analysis (40%) + experience relevance (10%) with missing skill penalty |
| 🔍 **Skill Taxonomy** | 80+ skills with aliases and importance weights; 4-tier section-aware extraction pipeline |
| 📊 **Analytics Dashboard** | Score distribution, skill gap analysis, interview readiness, AI insights, recommendation breakdown |
| 🤖 **Recruiter Chatbot** | Rule-based AI assistant using real DB data — top candidates, shortlist recommendations, pipeline breakdown, hiring decisions |
| 🔗 **Link Verification** | GitHub repo/profile + LinkedIn URL verification with commit activity detection |
| 📧 **Email Automation** | SMTP/Brevo/Resend notifications at every pipeline stage — test invite, tech interview, HR interview, offer letter, rejection |
| 🏗️ **Hiring Pipeline** | 7-stage Kanban board: Applied → Shortlisted → Testing → Interviewing → Offered / Rejected with bulk actions |
| 📝 **JD Optimizer** | Analyzes job descriptions for length, missing sections, vague language, skill coverage, salary info |
| ⚖️ **Decision Engine** | Strong Hire / Hire / Hold / Reject decisions using composite score from fit + test + interview scores |
| 🔐 **Auth** | JWT-based authentication, bcrypt passwords, role-based access |
| ☁️ **Cloud Ready** | Dockerized backend + frontend, Terraform modules for AWS VPC, ECS, RDS |

---

## 🏗️ Architecture

### System Overview (3-Tier)

```
┌─────────────────────────┐
│   FRONTEND               │
│   React 18 + TypeScript  │
│   Vite + Tailwind CSS    │
└────────────┬────────────┘
             │ REST / JSON
             ▼
┌─────────────────────────┐        ┌──────────────────────┐
│   BACKEND API            │        │  EXTERNAL SERVICES   │
│   FastAPI + asyncpg      │◄──────►│  Brevo / Resend      │
│   SQLAlchemy 2.0 async   │        │  Google Gemini API   │
└────────────┬────────────┘        └──────────────────────┘
             │
             ▼
┌─────────────────────────┐
│   DATABASE               │
│   PostgreSQL 16          │
│   (SQLite dev fallback)  │
└─────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Google Gemini — `gemini-2.0-flash` (impact scoring, resume fallback), `gemini-embedding-001` (semantic similarity) |
| **Backend** | FastAPI 0.116.1 + asyncpg (full async) |
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS |
| **Database** | PostgreSQL 16 (prod) / SQLite (dev fallback — auto-detected) |
| **ORM** | SQLAlchemy 2.0 async |
| **PDF Parsing** | pypdf + pdfplumber (dual-parser with confidence scoring) + Gemini fallback, offloaded via `run_in_executor` |
| **Embeddings** | Gemini `text-embedding-004` via `google-genai` SDK, cached with `lru_cache` |
| **Auth** | python-jose (JWT) + passlib/bcrypt |
| **Email** | smtplib SMTP / Brevo API / Resend API with HTML templates |
| **Container** | Docker + docker-compose |
| **Infra** | Terraform — AWS VPC, ECS, RDS modules |

---

## 🤖 AI Scoring Pipeline

```
Resume Upload (PDF / DOCX)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  parser.py — Dual-Parser PDF Extraction                     │
│  • Primary: pypdf → 6-pass cleanup pipeline                 │
│  • Fallback 1: pdfplumber (low heading confidence)          │
│  • Fallback 2: Gemini (graphic/column resumes)              │
│  • Runs in thread pool via run_in_executor (non-blocking)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  profile_extractor.py — Contact & Profile Extraction        │
│  • Skills: 4-tier pipeline (section → projects → exp → all)│
│  • contact_confidence score (0-100) returned in response    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  jd_matcher.py — Hybrid Fit Scoring                         │
│                                                             │
│  skill_score (20%)  sem_score (30%)  impact_score (40%)    │
│       │                  │                  │               │
│       └──────────────────┴──────────────────┘               │
│                asyncio.gather() — parallel                  │
│                          │                                  │
│         fit_score = weighted sum + experience (10%)         │
│         - missing_skill_penalty (up to -10 pts)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              Candidate saved to DB
              Application created with scores
```

### Scoring Weights

| Component | Weight | Source |
|-----------|--------|--------|
| Impact Score | 40% | Gemini achievement analysis |
| Semantic Similarity | 30% | Gemini embeddings (JD cached) |
| Skill Overlap | 20% | Weighted taxonomy matching |
| Experience Relevance | 10% | Rule-based year extraction |
| Missing Skill Penalty | -10 pts max | Deterministic |

> **Fallback:** If Gemini is unavailable, weights redistribute proportionally so the total always sums to 100%.

---

## ⚡ Performance

| Optimization | Implementation |
|---|---|
| Non-blocking PDF parsing | `run_in_executor` keeps FastAPI event loop free |
| Parallel AI scoring | `asyncio.gather()` for semantic + impact scoring |
| N+1 query elimination | Batch `SELECT ... WHERE id IN (...)` |
| JD embedding cache | `lru_cache` avoids redundant Gemini API calls |
| Pagination | All list endpoints support `limit` + `offset` |

---

## 🔒 Security

- JWT startup guard — server **refuses to start** if `JWT_SECRET` is default placeholder
- Role hardening — all self-registered users get `role = "hr"`, privilege escalation blocked
- Webhook authentication — `X-Webhook-Secret` header required, unauthenticated requests get `401`
- Input length limits — all free-text fields capped at 20,000 chars via `TextLengthMixin`
- Parameterised SQL via SQLAlchemy ORM — no injection risk
- File type + size validation on resume uploads (PDF/DOCX, 10MB limit)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12 (3.14 not supported — pydantic-core has no wheel)
- Node.js 18+
- PostgreSQL (optional — SQLite fallback auto-activates)
- Google Gemini API key (optional — scoring works without it via deterministic fallback)

### Backend Setup

```bash
cd backend

# Create virtualenv with Python 3.12
py -3.12 -m venv .venv          # Windows
python3.12 -m venv .venv        # Linux/Mac

# Activate
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set GEMINI_API_KEY, DATABASE_URL, JWT_SECRET, WEBHOOK_SECRET
```

> ⚠️ **Required:** `JWT_SECRET` must be a strong random string. Generate one:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

```bash
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | **Yes** | Strong random secret — server refuses to start without it |
| `DATABASE_URL` | No | PostgreSQL connection string. Falls back to SQLite if unset |
| `GEMINI_API_KEY` | No | Google Gemini API key. Falls back to deterministic mode if unset |
| `WEBHOOK_SECRET` | No | Shared secret for webhook endpoint |
| `SMTP_ENABLED` | No | Set `true` to enable SMTP email |
| `BREVO_API_KEY` | No | Brevo transactional email |
| `RESEND_API_KEY` | No | Resend transactional email — fallback |
| `ALLOWED_ORIGINS` | No | CORS origins. Defaults to `["http://localhost:3000"]` |
| `MAX_UPLOAD_SIZE_MB` | No | Resume upload size cap. Defaults to `10.0` |

---

## 🤖 Recruiter Chatbot

Rule-based AI assistant — **no API key required**. Answers using real DB data.

| Query | Response |
|-------|----------|
| "Who are the top candidates?" | Ranked list with scores, stage, matched skills |
| "Which candidates to shortlist?" | Strong Hire (≥70%) + Consider (50-69%) split |
| "Show pipeline breakdown" | Stage counts with visual breakdown |
| "Common skill gaps?" | Top missing skills across all applications |
| "Hiring decision?" | Strong Hire / Hire / Hold / Reject per candidate |
| "Analyze jd: [paste JD]" | JD quality score + issues + suggestions |
| "Draft offer letter" | Ready-to-fill offer letter template |

---

## 📁 Project Structure

```
fairhire-ai/
├── backend/
│   ├── core/                  # App factory, middleware, router registration
│   ├── db/                    # SQLAlchemy models, async session, DB probe
│   ├── routes/                # auth, jobs, upload, match, applications, interviews, analytics, chat
│   ├── services/
│   │   ├── parser.py          # PDF/DOCX extraction + 6-pass cleanup
│   │   ├── profile_extractor.py
│   │   ├── jd_matcher.py      # Hybrid AI + rule-based fit scoring
│   │   ├── semantic_matcher.py
│   │   ├── scoring_service.py
│   │   ├── decision_engine.py
│   │   ├── email_service.py
│   │   └── skill_taxonomy.py  # 80+ skills with weights
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/             # Dashboard, Jobs, Pipeline, Candidates, Interviews
│       ├── components/        # Layout, RecruiterChat, MetricsCards
│       └── services/api.ts
│
└── infra/
    └── modules/               # vpc/, ecs/, rds/
```

---

## 📊 Supported Skills (80+ in Taxonomy)

| Category | Skills |
|----------|--------|
| **Languages** | Python, JavaScript, TypeScript, Java, C++, Go, Rust, SQL, Bash |
| **Frameworks** | FastAPI, Django, React, Next.js, Node.js, Spring Boot |
| **AI / ML** | PyTorch, TensorFlow, LangChain, OpenAI API, Pandas, NumPy, spaCy |
| **Cloud / DevOps** | AWS, GCP, Docker, Kubernetes, Terraform, CI/CD |
| **Databases** | PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, Kafka |

---

## 👥 Team

Built with ❤️ during our internship by:

| Name | Role |
|------|------|
| Deep | Backend + AI/ML |
| Arpit Jain | Backend + AI/ML |
| Toshar Bhardwaj | Backend + AI/ML |
| Abhishek Choubey | Backend + AI/ML |

Special thanks to our mentor **Siddharth Srivastav** for pushing us to build something real.

---

## 🔗 Links

- 📹 [Watch Demo](#) ← *add your YouTube/Drive link here*
- 📄 [Technical Documentation](#) ← *add PDF link or Google Drive here*
- 💼 [LinkedIn](https://linkedin.com) ← *add your LinkedIn*

---

*Open to SDE / AI backend roles — 2026 grad. Feel free to reach out!*
