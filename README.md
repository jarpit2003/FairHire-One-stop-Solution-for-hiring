# FairHire AI

> Enterprise ATS-compliant hiring platform with AI-powered resume parsing, multi-stage pipeline management, and recruiter intelligence

FairHire AI is a full-stack Gen AI application that integrates **resume parsing**, **semantic embeddings**, **impact scoring**, **skill taxonomy matching**, **candidate deduplication**, **JD optimization**, **hiring decision engine**, **rule-based recruiter chatbot**, **email automation**, and **cloud deployment** — helping recruiters hire smarter, faster, and fairer.

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 📄 **Resume Parsing** | Upload PDF/DOCX → dual-parser pipeline (pypdf → pdfplumber → Gemini fallback) with 6-pass text cleanup; extracts name, email, phone, skills, education, certifications. Runs in a thread pool — never blocks the async event loop |
| 🧠 **AI Fit Scoring** | Hybrid scoring: weighted skill overlap (20%) + Gemini semantic embeddings (30%) + Gemini impact analysis (40%) + experience relevance (10%) with missing skill penalty |
| 🔍 **Skill Taxonomy** | 80+ skills with aliases and importance weights; 4-tier section-aware extraction pipeline (skills section → project stacks → experience → full text fallback) |
| 📊 **Analytics Dashboard** | Score distribution, skill gap analysis, interview readiness, AI insights, recommendation breakdown |
| 🤖 **Recruiter Chatbot** | Rule-based AI assistant using real DB data — top candidates, shortlist recommendations, pipeline breakdown, hiring decisions, JD analysis, resume tips |
| 🔗 **Link Verification** | GitHub repo/profile + LinkedIn URL verification with commit activity detection |
| 📧 **Email Automation** | SMTP/Brevo/Resend notifications at every pipeline stage — test invite, tech interview, HR interview, offer letter, rejection |
| 🏗️ **Hiring Pipeline** | Stage-grouped table view: Applied → Shortlisted → Testing → Interviewing → Offered / Rejected with bulk actions |
| 📝 **JD Optimizer** | Analyzes job descriptions for length, missing sections, vague language, skill coverage, salary info |
| ⚖️ **Decision Engine** | Strong Hire / Hire / Hold / Reject decisions using composite score from fit + test + interview scores |
| 🔐 **Auth** | JWT-based authentication, bcrypt passwords, role-based access. All users register as `hr` — privilege escalation on self-registration is blocked |
| ☁️ **Cloud Ready** | Dockerized backend + frontend, Terraform modules for AWS VPC, ECS, RDS |

---

## 🏗️ Architecture

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
│  • Email: contact zone scan → normalize spaced emails →     │
│    validate domain → prefer non-edu → fallback full text    │
│  • Phone: 10-15 digit validation → reject year ranges       │
│  • Name: ALL CAPS + hyphenated + title case support         │
│  • Skills: 4-tier pipeline (section → projects → exp → all)│
│  • Education, Certifications, Experience years              │
│  • contact_confidence score (0-100) returned in response    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  jd_matcher.py — Hybrid Fit Scoring                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ skill_score │  │ sem_score    │  │ impact_score     │  │
│  │             │  │              │  │                  │  │
│  │ Weighted    │  │ Gemini       │  │ Gemini analyzes  │  │
│  │ taxonomy    │  │ embeddings   │  │ achievement      │  │
│  │ overlap     │  │ cosine sim   │  │ sentences        │  │
│  │ (SKILL_     │  │ JD cached    │  │ scores impact    │  │
│  │  WEIGHTS)   │  │ lru_cache    │  │ per sentence     │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                │                    │            │
│         └────────────────┼────────────────────┘            │
│                          │  asyncio.gather() — parallel    │
│                          ▼                                  │
│         fit_score = weighted sum (redistributes if          │
│                    Gemini unavailable)                      │
│         - missing_skill_penalty (up to -10 pts)            │
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

> **Fallback:** If Gemini is unavailable, weights are redistributed proportionally across remaining active components so total always sums to 100%.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register HR user (role hardcoded to `hr`) |
| `POST` | `/api/v1/auth/login` | Login → JWT token |
| `GET` | `/api/v1/auth/me` | Current user profile |
| `GET` | `/api/v1/jobs/` | List all jobs |
| `POST` | `/api/v1/jobs/` | Create job requisition |
| `POST` | `/api/v1/jobs/{id}/publish` | Publish to LinkedIn/Naukri/X |
| `POST` | `/api/v1/upload/resume` | Upload + parse + score resume (async, non-blocking) |
| `POST` | `/api/v1/match/jd` | Score candidate against JD |
| `GET` | `/api/v1/applications/?job_id=&limit=&offset=` | List applications with pagination |
| `PATCH` | `/api/v1/applications/{id}/stage` | Advance pipeline stage |
| `POST` | `/api/v1/applications/{id}/offer` | Send offer letter |
| `POST` | `/api/v1/applications/{id}/reject` | Send rejection email |
| `POST` | `/api/v1/applications/{id}/send-test-link` | Send assessment link |
| `POST` | `/api/v1/applications/{id}/test-score` | Record test score |
| `GET` | `/api/v1/applications/{id}/offer-draft` | AI-generated offer letter draft |
| `POST` | `/api/v1/applications/webhook/test-score` | Webhook for test platforms (requires `X-Webhook-Secret` header) |
| `GET` | `/api/v1/candidates/?limit=&offset=` | List candidates with pagination |
| `GET` | `/api/v1/candidates/{id}` | Candidate profile |
| `POST` | `/api/v1/interviews/` | Schedule interview |
| `GET` | `/api/v1/interviews/?job_id=&limit=&offset=` | List interviews with pagination |
| `PATCH` | `/api/v1/interviews/{id}/score` | Submit interview score |
| `PATCH` | `/api/v1/interviews/{id}/status` | Update interview status |
| `POST` | `/api/v1/analytics/summary` | Dashboard analytics |
| `POST` | `/api/v1/chat/` | Recruiter chatbot |

---

## 🤖 Recruiter Chatbot

Rule-based AI assistant — **no API key required**. Answers using real DB data.

| Query | Response |
|-------|----------|
| "Who are the top candidates?" | Ranked list with scores, stage, matched skills |
| "Which candidates to shortlist?" | Strong Hire (≥70%) + Consider (50-69%) split |
| "Show pipeline breakdown" | Stage counts with visual bar chart |
| "Common skill gaps?" | Top missing skills across all applications |
| "Hiring decision?" | Strong Hire / Hire / Hold / Reject per candidate |
| "Why were candidates rejected?" | Rejected list with scores and missing skills |
| "Analyze jd: [paste JD]" | JD quality score + issues + suggestions |
| "How to improve resumes?" | Missing skills + general resume tips |
| "Write interview questions for React dev" | Technical + behavioural + culture fit questions |
| "Draft offer letter" | Ready-to-fill offer letter template |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12 (3.14 not supported — pydantic-core has no wheel)
- Node.js 18+
- PostgreSQL (optional — SQLite fallback auto-activates)
- Google Gemini API key (optional — scoring works without it using deterministic fallback)

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

> ⚠️ **Required:** `JWT_SECRET` must be set to a strong random string. The server will **refuse to start** if it is left as the default placeholder.
> Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"`

```bash
# Start server
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

### Demo Login
```
Register a new account at http://localhost:3000
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | **Yes** | Strong random secret for signing JWT tokens. Server refuses to start without it |
| `DATABASE_URL` | No | PostgreSQL connection string. Falls back to SQLite if unset or unreachable |
| `GEMINI_API_KEY` | No | Google Gemini API key. Scoring falls back to deterministic mode if unset |
| `WEBHOOK_SECRET` | No | Shared secret for `POST /webhook/test-score`. Requests without it are rejected with 401 |
| `SMTP_ENABLED` | No | Set `true` to enable SMTP email sending |
| `SMTP_HOST` / `SMTP_USERNAME` / `SMTP_PASSWORD` | No | SMTP credentials (Gmail, etc.) |
| `BREVO_API_KEY` | No | Brevo (Sendinblue) transactional email — alternative to SMTP |
| `RESEND_API_KEY` | No | Resend transactional email — fallback |
| `ALLOWED_ORIGINS` | No | CORS origins list. Defaults to `["http://localhost:3000"]` |
| `MAX_UPLOAD_SIZE_MB` | No | Resume upload size cap. Defaults to `10.0` |

See `backend/.env.example` for a full template.

---

## ☁️ Infrastructure (Terraform)

```bash
cd infra
terraform init
terraform plan
terraform apply
```

Provisions: AWS VPC + subnets + security groups, ECS cluster + task definitions, RDS PostgreSQL instance.

---

## 📊 Supported Skills (80+ in Taxonomy)

| Category | Skills |
|----------|--------|
| **Languages** | Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, SQL, Bash |
| **Frameworks** | FastAPI, Django, Flask, React, Next.js, Vue.js, Angular, Node.js, Spring Boot, Express |
| **AI / ML** | PyTorch, TensorFlow, scikit-learn, Hugging Face, LangChain, OpenAI API, Pandas, NumPy, OpenCV, spaCy |
| **Cloud / DevOps** | AWS, GCP, Azure, Docker, Kubernetes, Terraform, CI/CD, Nginx, Linux |
| **Databases** | PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, Kafka, RabbitMQ, Prisma, Supabase |
| **Frontend** | Tailwind CSS, Redux, Webpack, Vite |
| **Testing** | Jest, Pytest, Selenium, Playwright, Cypress |
| **Tools** | Git, Figma, Postman, Jira |

---

## 📁 Project Structure

```
fairhire-ai/
├── backend/
│   ├── core/                  # App factory, middleware, router registration
│   ├── db/                    # SQLAlchemy models, async session, DB probe
│   ├── embeddings/            # Gemini embedding wrapper
│   ├── routes/                # API route handlers
│   │   ├── auth.py            # Register / login / JWT
│   │   ├── jobs.py            # Job CRUD + publish to platforms
│   │   ├── upload.py          # Resume upload, parse (async), profile, quality score
│   │   ├── match.py           # JD fit scoring
│   │   ├── applications.py    # Pipeline stage management + webhook
│   │   ├── interviews.py      # Schedule + score interviews
│   │   ├── analytics.py       # Dashboard analytics
│   │   └── chat.py            # Recruiter chatbot
│   ├── services/
│   │   ├── parser.py          # PDF/DOCX extraction + 6-pass cleanup
│   │   ├── profile_extractor.py  # Contact + skills + education extraction
│   │   ├── jd_matcher.py      # Hybrid AI + rule-based fit scoring
│   │   ├── semantic_matcher.py   # Gemini embeddings + cosine similarity
│   │   ├── scoring_service.py    # Gemini impact scoring
│   │   ├── analytics.py       # Analytics computation + AI insights
│   │   ├── skill_taxonomy.py  # 80+ skills with weights
│   │   ├── resume_quality.py  # Resume quality scorer (0-100)
│   │   ├── jd_optimizer.py    # JD quality analyzer
│   │   ├── decision_engine.py # Hiring decision engine
│   │   ├── email_service.py   # SMTP/Brevo/Resend email templates
│   │   ├── workflow_service.py   # Pipeline stage orchestration
│   │   ├── link_verifier.py   # GitHub/LinkedIn URL verification
│   │   └── interview_questions.py  # Question generator
│   ├── scripts/               # Dev/debug utilities (not deployed)
│   ├── main.py
│   ├── config.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # Dashboard, Jobs, Pipeline, Candidates, Interviews, Login
│   │   ├── components/        # Layout, RecruiterChat, WelcomeBanner, MetricsCards
│   │   ├── context/           # Auth, Job, Pipeline context providers
│   │   └── services/api.ts    # Axios API client
│   ├── tailwind.config.js     # Emerald dark glass theme
│   └── vite.config.ts
│
└── infra/
    ├── main.tf
    └── modules/               # vpc/, ecs/, rds/
```

---

## 🔒 Security

- **Role hardening** — all self-registered users get `role = "hr"`. Privilege escalation via the register endpoint is blocked server-side
- **JWT startup guard** — server refuses to start if `JWT_SECRET` is the default placeholder value
- **Webhook authentication** — `POST /webhook/test-score` requires a valid `X-Webhook-Secret` header; unauthenticated requests receive `401`
- **Input length limits** — all free-text fields (`description`, `notes`, `feedback`, `resume_text`) are capped at 20,000 characters via `TextLengthMixin` to prevent Gemini quota abuse
- **JWT authentication** — bcrypt passwords, HS256 tokens, 8-hour expiry
- **Pydantic input validation** on all endpoints
- **Parameterised SQL** via SQLAlchemy ORM (no injection risk)
- **CORS** restricted to configured origins
- **File type + size validation** on resume uploads (PDF/DOCX, 10MB limit)
- **Email/phone masked** during PDF cleanup to prevent data corruption
- **Fake domain rejection** in email extraction
- **SQLite auto-fallback** if PostgreSQL unavailable (dev safety net)

---

## ⚡ Performance

- **Non-blocking PDF parsing** — `parse_resume()` runs in a thread pool via `asyncio.run_in_executor`, keeping the FastAPI event loop free during CPU-bound PDF extraction
- **Batch candidate loading** — `list_applications` loads all candidates in a single `SELECT ... WHERE id IN (...)` query, eliminating the previous N+1 pattern
- **Parallel AI scoring** — semantic similarity and impact scoring run concurrently via `asyncio.gather()`
- **Pagination** — all list endpoints (`/applications/`, `/candidates/`, `/interviews/`) support `limit` and `offset` query parameters (default: `limit=100`)
- **JD embedding cache** — Gemini JD embeddings are cached with `lru_cache` to avoid redundant API calls within a process

---

## 🛠️ Development Scripts

Utility and debug scripts live in `backend/scripts/` and are excluded from production deployments via `.gitignore`.

```
backend/scripts/
├── check_health.py        # Verify server is running
├── test_gemini.py         # Test Gemini API connectivity
├── test_links.py          # Test link verifier
├── smtp_test.py           # Test SMTP email sending
├── pg_check.py            # Verify PostgreSQL connection
├── migrate_interviews.py  # One-time interview table migration
├── clean_duplicates.py    # Remove duplicate candidate records
├── verify_*.py            # Sprint verification scripts
└── debug_*.py             # Route-level debug helpers
```
