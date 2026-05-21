# FairHire AI - Complete Project Flowcharts
# Open each mermaid block at https://mermaid.live

---

## FLOWCHART 1 - Full System Architecture

```mermaid
flowchart TD
    subgraph CLIENT["FRONTEND - React + TypeScript + Vite"]
        LAND[Landing Page]
        LOGIN[Login Page - Email/Password - Google OAuth]
        DASH[Dashboard - Metrics + Analytics]
        JOBS[Jobs Page - Create / Publish]
        PIPE[Pipeline Page - Stage Management]
        CANDS[Candidates Page]
        PROF[Candidate Profile]
        INTV[Interviews Page]
        PROC[Process Resumes]
        CHAT[RecruiterChat - Floating Widget]
    end

    subgraph AUTH_FLOW["AUTH LAYER"]
        JWT[JWT Token - HS256 - 8hr expiry]
        GOOG[Google OAuth2 - Authorization Code Flow]
    end

    subgraph BACKEND["BACKEND - FastAPI + asyncpg"]
        subgraph ROUTES["API Routes /api/v1/"]
            R_AUTH[auth - register login google]
            R_JOBS[jobs - CRUD publish]
            R_UPLOAD[upload/resume - Parse + Profile]
            R_MATCH[match/jd - Fit Scoring]
            R_APPS[applications - Pipeline CRUD]
            R_INTV[interviews - Schedule + Score]
            R_CHAT[chat - Chatbot]
            R_ANAL[analytics/summary]
            R_INTAKE[intake/submit - Public API]
            R_APPLY[apply/job_id - Public HTML Form]
        end

        subgraph SERVICES["Services Layer"]
            SVC_PARSE[parser.py - pypdf to pdfplumber]
            SVC_PROF[profile_extractor.py - Regex Pipeline]
            SVC_JD[jd_matcher.py - Hybrid Scoring]
            SVC_SEM[semantic_matcher.py - BM25 TF-IDF]
            SVC_IMP[scoring_service.py - Impact Scorer]
            SVC_TAX[skill_taxonomy.py - 80+ Skills]
            SVC_DEC[decision_engine.py - Hire/Hold/Reject]
            SVC_EMAIL[email_service.py - Brevo/Resend/SMTP]
            SVC_JDO[jd_optimizer.py - JD Quality]
            SVC_QUAL[resume_quality.py - 0-100 Score]
            SVC_LINK[link_verifier.py - GitHub/LinkedIn]
        end
    end

    subgraph DB["PostgreSQL - 6 Tables"]
        T_USERS[(hr_users)]
        T_JOBS[(jobs)]
        T_CANDS[(candidates)]
        T_APPS[(applications)]
        T_INTV[(interviews)]
        T_FORMS[(form_submissions)]
    end

    LOGIN -->|email + password| R_AUTH
    LOGIN -->|OAuth code| GOOG
    GOOG -->|exchange code| R_AUTH
    R_AUTH --> JWT
    JWT -->|stored in localStorage| CLIENT

    PROC --> R_UPLOAD
    JOBS --> R_JOBS
    PIPE --> R_APPS
    CANDS --> R_MATCH
    INTV --> R_INTV
    CHAT --> R_CHAT
    DASH --> R_ANAL

    R_UPLOAD --> SVC_PARSE
    SVC_PARSE --> SVC_PROF
    SVC_PROF --> SVC_TAX
    SVC_PROF --> SVC_LINK
    SVC_PROF --> SVC_QUAL

    R_MATCH --> SVC_JD
    SVC_JD --> SVC_SEM
    SVC_JD --> SVC_IMP
    SVC_JD --> SVC_TAX

    R_APPS --> SVC_DEC
    R_APPS --> SVC_EMAIL
    R_CHAT --> SVC_DEC
    R_CHAT --> SVC_JDO

    R_APPLY --> R_INTAKE
    R_INTAKE --> SVC_PROF
    R_INTAKE --> SVC_JD
    R_INTAKE --> SVC_EMAIL

    BACKEND --> DB
```

---

## FLOWCHART 2 - Server Startup Sequence

```mermaid
flowchart TD
    A([uvicorn main:app --reload]) --> B[create_app]
    B --> C[register_middleware - CORS + Request-ID header]
    C --> D[register_routers - 13 route modules mounted]
    D --> E{lifespan startup}
    E --> F[probe_postgres - NullPool test connection]
    F --> G{Connection OK?}
    G -->|Yes| H[Use PostgreSQL URL]
    G -->|No| I[Fallback to SQLite - sqlite+aiosqlite://./fairhire.db]
    H --> J[init_engine - Create AsyncEngine + SessionFactory]
    I --> J
    J --> K[Base.metadata.create_all - Create all 6 tables if missing]
    K --> L{JWT_SECRET == default?}
    L -->|Yes| M[RuntimeError - Server refuses to start]
    L -->|No| N[Server Ready - localhost:8000]
    N --> O[Swagger UI at /docs]
    N --> P[Health check at /health]
```

---

## FLOWCHART 3 - Authentication Flow

```mermaid
flowchart TD
    subgraph EMAIL_AUTH["Email and Password Auth"]
        A1[User fills Login form] --> B1{Mode?}
        B1 -->|Register| C1[POST /auth/register - email password full_name]
        B1 -->|Login| D1[POST /auth/login - OAuth2PasswordRequestForm]
        C1 --> E1[hash_password - passlib bcrypt]
        E1 --> F1[Save HRUser - role hardcoded = hr]
        D1 --> G1[verify_password - bcrypt compare]
        G1 -->|Match| H1[create_access_token - python-jose HS256]
        F1 --> H1
        H1 --> I1[Return JWT - user_id email role]
        I1 --> J1[Store in localStorage - quantumlogic_token]
    end

    subgraph GOOGLE_AUTH["Google OAuth2 Flow"]
        A2[Click Continue with Google] --> B2[Redirect to accounts.google.com - scope openid email profile]
        B2 --> C2[User picks Google account]
        C2 --> D2[Google redirects to /auth/google/callback?code=XXX]
        D2 --> E2[GoogleCallback.tsx - extracts code from URL]
        E2 --> F2[POST /auth/google - credential: code]
        F2 --> G2[httpx POST to oauth2.googleapis.com/token - exchange code for id_token]
        G2 --> H2[id_token.verify_oauth2_token - google-auth library]
        H2 -->|Valid| I2{User exists?}
        I2 -->|No| J2[Create HRUser - role = hr]
        I2 -->|Yes| K2[Fetch existing user]
        J2 --> L2[create_access_token]
        K2 --> L2
        L2 --> M2[Return JWT]
        M2 --> N2[Navigate to /dashboard]
    end

    subgraph PROTECTED["Every Protected Request"]
        P1[Request with Authorization Bearer TOKEN] --> P2[get_current_user dependency]
        P2 --> P3[decode_token - python-jose]
        P3 -->|Invalid or Expired| P4[401 Unauthorized - Frontend clears localStorage]
        P3 -->|Valid| P5[db.get HRUser by sub]
        P5 --> P6[Route handler executes]
    end
```

---

## FLOWCHART 4 - Resume Upload and Parsing Pipeline

```mermaid
flowchart TD
    A([HR uploads PDF/DOCX - POST /upload/resume]) --> B{File type valid? PDF DOC DOCX}
    B -->|No| C[415 Unsupported Media Type]
    B -->|Yes| D{Size under 10MB?}
    D -->|No| E[413 Too Large]
    D -->|Yes| F[run_in_executor - Thread Pool - non-blocking]

    F --> G{File type?}
    G -->|PDF| H[pypdf - extract_text all pages]
    G -->|DOCX| I[python-docx - paragraphs + tables + headers]
    G -->|DOC| J[latin-1 decode]

    H --> K[_score_headings - count Skills/Experience/Education/Projects/Certs]
    K --> L{headings >= 2?}
    L -->|No - low confidence| M[pdfplumber fallback - better for multi-column]
    L -->|Yes| N[Use pypdf output]
    M --> O{pdfplumber better?}
    O -->|Yes| P[Use pdfplumber output - used_fallback=True]
    O -->|No| N

    N --> Q[6-Pass Cleanup Pipeline]
    P --> Q

    subgraph CLEANUP["6-Pass Text Cleanup"]
        Q1[Pass 1 - Unicode NFC normalise - Bullets/dashes to ASCII]
        Q2[Pass 2 - Strip decorative symbols - Box-drawing dingbats icon fonts]
        Q3[Pass 3 - Restore missing spaces - CamelCase commas slashes - Emails/phones masked first]
        Q4[Pass 3b - Rejoin ALL-CAPS broken words - RELEV ANT to RELEVANT]
        Q5[Pass 4 - Rejoin words split across lines - lowercase-newline-lowercase]
        Q6[Pass 5 - Isolate section headings onto their own lines]
        Q7[Pass 6 - Whitespace collapse - trailing spaces blank lines]
        Q1 --> Q2 --> Q3 --> Q4 --> Q5 --> Q6 --> Q7
    end

    Q --> Q1
    Q7 --> R[extract_profile - Profile Extractor]
    Q7 --> S[verify_links - GitHub + LinkedIn]
    Q7 --> T[compute_resume_quality - 0-100 score]

    R --> U[Return UploadResponse - full_text profile_summary verified_links resume_quality contact_confidence]
```

---

## FLOWCHART 5 - Profile Extraction Regex Pipeline

```mermaid
flowchart TD
    A([Cleaned resume text]) --> B[extract_profile]

    subgraph CONTACT["Contact Extraction"]
        B --> C[_contact_zone - First 25 lines + signal lines]
        C --> D[_normalize_contact_text - Strip emoji icons - fix spaced @ - handle at obfuscation]
        D --> E[_extract_email - 3-pass: zone to full text to aggressive]
        D --> F[_extract_phone - 10-15 digits - reject year patterns]
        D --> G[_extract_name - First 15 lines - ALL CAPS - title case - Fallback from email]
        E --> H[contact_confidence - 0-100 score]
    end

    subgraph SKILLS["4-Tier Skill Extraction"]
        B --> S1[Tier 1 - Skills section - _SKILL_HEADING regex slice]
        S1 --> S2[Tier 2 - Project tech-stack lines - Technologies used - Built with]
        S2 --> S3[Tier 3 - Experience section]
        S3 --> S4[Tier 4 - Full text fallback]
        S4 --> S5[Match against SKILL_TAXONOMY - 80+ skills with aliases - compiled re.Pattern objects]
    end

    subgraph EDU["Education Extraction"]
        B --> E1[Slice education section - _EDU_HEADING regex]
        E1 --> E2[_DEGREE_PATTERN - B.Tech Bachelor Master PhD]
        E2 --> E3[_FIELD_PATTERN - only inside edu section - CS IT Data Science]
    end

    subgraph CERT["Certification Extraction"]
        B --> C1[_CERT_PATTERN anywhere - AWS Certified CKA PMP CISSP]
        C1 --> C2[Achievement section lines - _ACHIEVEMENT_SIGNAL - awarded winner ranked certificate]
    end

    subgraph EXP["Experience Years"]
        B --> X1[Explicit - 5+ years of experience]
        X1 --> X2[Date ranges - Jan 2020 to Present - calculate span - clamp to current year]
        X2 --> X3[Max of all spans found]
    end

    S5 --> RESULT[CandidateProfile - skills education certifications experience_years name email phone]
    E3 --> RESULT
    C2 --> RESULT
    X3 --> RESULT
    H --> RESULT
```

---

## FLOWCHART 6 - AI Fit Scoring Pipeline

```mermaid
flowchart TD
    A([POST /match/jd - CandidateProfile + JD text]) --> B[match_candidate_to_jd]

    B --> C[_extract_jd_skills - Regex match SKILL_TAXONOMY against JD]
    C --> D[matched = profile.skills intersect jd_skills - missing = jd_skills minus profile.skills]

    D --> E[skill_score - weighted_match / weighted_total - SKILL_WEIGHTS per skill]
    D --> F[experience_score - smooth sqrt curve - 0.5 if no data]
    D --> G[education_score - degree level + field match - 0.5 if no data]
    D --> H[build_profile_text - skills + edu stripped of institution names + cert names + experience tier]

    H --> I[asyncio.gather - PARALLEL]

    subgraph PARALLEL["Run Concurrently"]
        I --> J[semantic_similarity - BM25 TF-IDF cosine]
        I --> K[score_impact - Deterministic sentence scorer]
    end

    subgraph BM25["BM25 TF-IDF - semantic_matcher.py"]
        J --> J1[_tokenise - lowercase - remove stopwords]
        J1 --> J2[BM25 term saturation - TF_sat = count / count + k x length_norm]
        J2 --> J3[IDF lookup table - kubernetes=3.8 python=2.2 api=1.6]
        J3 --> J4[_bm25_vector_cached - lru_cache maxsize=128]
        J4 --> J5[_cosine similarity - dot product / magnitude product]
    end

    subgraph IMPACT["Impact Scorer - scoring_service.py"]
        K --> K1[_extract_achievement_sentences - Split on . ! ? and newlines - Filter by _ACHIEVEMENT_RE]
        K1 --> K2[Score each sentence 0-10 - +4 strong quant pct x ms users - +2 weak quant projects bugs - +2 strong verb led architected - +1 per JD keyword max 3 - +1 if 12+ words - -3 weak filler responsible for]
        K2 --> K3[mean of ALL sentences + excellence bonus if top score >= 8]
    end

    E --> L[Weighted Sum - skill x0.30 + sem x0.25 + impact x0.25 + exp x0.10 + edu x0.10]
    F --> L
    G --> L
    J5 --> L
    K3 --> L

    L --> M[missing_penalty - sqrt missing_ratio x 0.12 - non-linear fairer than linear]
    M --> N[cert_bonus - 0-5 pts for relevant certs - no certs = 0 not penalised]
    N --> O[fit_score = raw x100 minus penalty + bonus - clamped 0-100]

    O --> P[MatchResult - fit_score matched_skills missing_skills all component scores impact_highlights]
```

---

## FLOWCHART 7 - Hiring Pipeline Stage Machine

```mermaid
flowchart TD
    A([Candidate Applies]) --> B[applied]

    B -->|HR reviews score| C{Score threshold?}
    C -->|above threshold| D[shortlisted]
    C -->|too low| REJ[rejected - Rejection email sent]

    D -->|Send assessment| E[testing - Test link email sent]
    D -->|Skip test| F[interviewing]
    E -->|Score recorded via webhook or manual| F

    F -->|Final decision| G{Decision Engine}
    G -->|composite >= 80 pct - skill coverage >= 70 pct| H[Strong Hire]
    G -->|composite >= 65 pct - skill coverage >= 50 pct| I[Hire]
    G -->|composite >= 50 pct| J[Hold]
    G -->|composite < 50 pct| REJ

    H --> K[offered - Offer letter sent]
    I --> K
    K -->|Rescind| REJ
    REJ -->|Re-open| B

    subgraph SCORES["Score Components on Application"]
        SC1[resume_score - AI fit score]
        SC2[test_score - assessment result]
        SC3[interview_score - round 1]
        SC4[hr_interview_score - round 2]
        SC5[final_score - weighted composite]
    end

    subgraph WEBHOOK["Test Score Webhook"]
        W1[POST /applications/webhook/test-score - X-Webhook-Secret header required]
        W1 --> W2[Validate secret - 401 if missing or wrong]
        W2 --> W3[record_test_score - advance to testing stage]
    end
```

---

## FLOWCHART 8 - Public Application Form Flow

```mermaid
flowchart TD
    A([Candidate visits GET /apply/job_id]) --> B[Serve pure HTML form - no React no auth needed]
    B --> C[Candidate fills Name Email Phone LinkedIn Resume text Cover note]
    C --> D[POST /apply/job_id/submit - Form data]

    D --> E[intake_submit]
    E --> F{Job exists?}
    F -->|No| G[404 Job not found]
    F -->|Yes| H[Build full_resume - resume_text + LinkedIn + cover note]

    H --> I[candidate_service.create - Upsert by email no duplicates - Stores linkedin_url]

    I --> J{Duplicate application?}
    J -->|Yes| K[Return existing application - email_sent=False]
    J -->|No| L[Score resume against JD - extract_profile then match_candidate_to_jd]

    L --> M[application_service.create - Save to applications table]
    M --> N[FormSubmission record - Raw audit log immutable - Saved to form_submissions table]
    N --> O[send_application_acknowledgement - Brevo/Resend/SMTP]
    O --> P[Return IntakeResponse - candidate_id application_id resume_score email_sent]

    P --> Q{Via HTML form?}
    Q -->|Yes| R[Show success message on same HTML page]
    Q -->|No - API| S[JSON response]
```

---

## FLOWCHART 9 - Recruiter Chatbot Flow

```mermaid
flowchart TD
    A([HR types message - POST /chat/]) --> B[_intent detection - Regex pattern matching]

    B --> C{Intent?}

    C -->|top best highest + candidate| D[_handle_top_candidates - Query DB sort by final_score - Return top 5 with scores]
    C -->|shortlist who to interview| E[_handle_shortlist - Strong Hire >=70 pct - Consider 50-69 pct]
    C -->|stage pipeline breakdown| F[_handle_pipeline - Count per stage - ASCII bar chart]
    C -->|missing skill skill gap| G[_handle_skill_gaps - Counter on all missing_skills - Top 7 most common]
    C -->|decision should hire| H[_handle_hiring_decision - Run decision_engine.make_decision per candidate]
    C -->|analyze jd: text| I[_handle_jd_analysis - jd_optimizer.analyze_jd - Score + issues + suggestions]
    C -->|interview questions for X| J[_handle_interview_questions - Technical + Behavioural + Culture Fit template]
    C -->|offer letter draft offer| K[_handle_offer_letter - Ready-to-fill template]
    C -->|why rejected| L[_handle_why_rejected - Rejected list with scores and missing skills]
    C -->|improve resume| M[_handle_improve_resume - Top skill gaps + general tips]
    C -->|hi hello help| N[_handle_greeting - Capabilities list]

    D --> Z[ChatResponse.reply - Markdown formatted text]
    E --> Z
    F --> Z
    G --> Z
    H --> Z
    I --> Z
    J --> Z
    K --> Z
    L --> Z
    M --> Z
    N --> Z
```

---

## FLOWCHART 10 - Frontend Navigation and State

```mermaid
flowchart TD
    subgraph PROVIDERS["Context Providers wrap entire app"]
        P1[AuthProvider - user token login googleLogin logout - 401 interceptor]
        P2[JobProvider - active job persisted in localStorage]
        P3[PipelineProvider - pipeline stage data]
    end

    A([User visits app]) --> B{isAuthenticated?}
    B -->|No| C[Landing Page /]
    C --> D[Login Page /login]
    D -->|Email/Password| E[AuthContext.login - POST /auth/login]
    D -->|Google button| F[Redirect to Google OAuth]
    F --> G[/auth/google/callback - GoogleCallback.tsx - spinner while processing]
    G --> H[AuthContext.googleLogin - POST /auth/google]

    E --> I[JWT stored - Navigate to /dashboard]
    H --> I
    B -->|Yes| I

    I --> J[Dashboard - Metrics Score distribution Top candidates AI insights]
    J --> K[Jobs Page - Create job Set JD Publish]
    K --> L[Process Resumes - Upload PDF/DOCX - See profile + score]
    L --> M[Pipeline Page - Stage-grouped table - Advance Reject Offer]
    M --> N[Candidates Page - All candidates list]
    N --> O[Candidate Profile - Full details scores links]
    M --> P[Interviews Page - Schedule Score rounds]
    J --> Q[RecruiterChat - Floating widget - always visible when logged in]

    subgraph AXIOS["Axios API Client - services/api.ts"]
        AX1[Base URL: /api/v1]
        AX2[JWT injected in Authorization header]
        AX3[401 response clears auth - auto logout]
    end
```

---

## FLOWCHART 11 - Email Notification System

```mermaid
flowchart TD
    A([Email trigger event]) --> B{Which provider is configured?}

    B -->|BREVO_API_KEY set| C[Brevo API - HTTP POST to api.brevo.com - Works behind corporate firewalls - Sends to any address]
    B -->|RESEND_API_KEY set| D[Resend API - HTTP POST to api.resend.com - Fallback provider]
    B -->|SMTP_ENABLED=true| E[smtplib SMTP - starttls login sendmail - Often blocked on corporate networks]
    B -->|Nothing configured| F[Log warning - Skip silently - Return False]

    C --> G{Send success?}
    D --> G
    E --> G

    G -->|Yes| H[Return True - email_sent=True in response]
    G -->|No| I[Log error - Return False]

    subgraph TRIGGERS["Email Trigger Points"]
        T1[Intake form submitted - Acknowledgement email]
        T2[PATCH stage to testing - Test link email]
        T3[POST /reject - Rejection email]
        T4[POST /offer - Offer letter email]
        T5[Interview scheduled - Interview invite]
    end
```

---

## FLOWCHART 12 - Database Write Flow

```mermaid
flowchart TD
    subgraph WRITES["Every DB Write Path"]
        W1[Register user - hr_users INSERT]
        W2[Create job - jobs INSERT]
        W3[Upload resume + match - candidates UPSERT - applications UPSERT]
        W4[Intake form submit - candidates UPSERT - applications UPSERT - form_submissions INSERT]
        W5[Advance stage - applications UPDATE stage]
        W6[Record test score - applications UPDATE test_score - recompute final_score]
        W7[Record interview score - applications UPDATE interview_score - recompute final_score]
        W8[Schedule interview - interviews INSERT]
        W9[Reject or Offer - applications UPDATE stage+status]
    end

    subgraph FINAL_SCORE["final_score Recomputation"]
        FS1[resume_score x resume_weight]
        FS2[test_score x test_weight]
        FS3[interview_score x test_weight]
        FS4[hr_interview_score x resume_weight/2]
        FS1 --> FS5[weighted_sum / total_weight]
        FS2 --> FS5
        FS3 --> FS5
        FS4 --> FS5
    end

    subgraph DEDUP["Candidate Deduplication"]
        D1[New submission arrives - email: john@gmail.com]
        D1 --> D2{SELECT WHERE email=X OR phone=Y}
        D2 -->|Found| D3[UPDATE existing - full_name resume_text linkedin_url phone]
        D2 -->|Not found| D4[INSERT new Candidate]
    end
```
