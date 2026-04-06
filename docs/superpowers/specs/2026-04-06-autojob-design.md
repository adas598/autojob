# AutoJob — Design Specification

Personal job application dashboard that scrapes job portals, scores listings against your resume using an LLM rubric, and generates tailored resumes for applications.

## 1. Architecture

**Deployment:** Vercel (frontend) + Railway (backend + database)

- **Frontend:** Next.js + Tailwind CSS on Vercel free tier
- **Backend:** FastAPI monolith on Railway free tier ($5/mo credit)
- **Database:** PostgreSQL on Railway
- **Auth:** Clerk OAuth

### Data Flow

1. **Scrape:** APScheduler triggers Playwright → scrapes 5 portals → raw jobs stored in PostgreSQL
2. **Match:** New jobs → LLM rubric scores each against active resume → score + reasoning saved
3. **Notify:** Jobs above threshold → Telegram bot sends digest with dashboard links
4. **Apply:** User picks job → GPT 5.4 tailors resume content → LaTeX compiles PDF → browser opens application page

### Backend Components

| Component | Tech | Purpose |
|-----------|------|---------|
| API server | FastAPI (async) | REST endpoints for frontend |
| Scheduler | APScheduler | Configurable cron: 12h / daily / weekly |
| Scraper | Playwright (async) | Headless browser, one module per portal |
| Matcher | LangChain + GPT 5.4 | LLM rubric scoring |
| Resume parser | PyMuPDF | PDF text + structured extraction |
| Resume generator | LangChain + pdflatex | Tailored content → LaTeX → PDF |
| Notifier | python-telegram-bot | Job alert digests |
| ORM | SQLAlchemy (async) + Alembic | Models + migrations via asyncpg |

## 2. Job Portals

Five portals, each with a dedicated scraper module sharing a base interface:

| Portal | Module | Notes |
|--------|--------|-------|
| LinkedIn | `linkedin.py` | Most aggressive anti-scraping; needs careful rate limiting |
| Indeed | `indeed.py` | High volume, structured listings |
| Glassdoor | `glassdoor.py` | Jobs + company metadata |
| Wellfound | `wellfound.py` | Startup/tech focused |
| Seek.com.au | `seek.py` | Australian market |

**Scraper interface:** Each module implements `async scrape(keywords, location) -> list[RawJob]`. Adding a new portal means adding one file that implements this interface.

**Dedup:** Jobs are deduplicated on `(portal, external_id)` unique constraint. Re-scraping updates `scraped_at` without creating duplicates.

## 3. Database Schema

7 tables in PostgreSQL:

### resumes
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| file_name | VARCHAR | |
| raw_text | TEXT | Full extracted text |
| parsed_skills | JSONB | `["Python", "AWS", ...]` |
| parsed_experience | JSONB | `[{title, company, dates, desc}]` |
| parsed_education | JSONB | `[{degree, institution, year}]` |
| pdf_blob | BYTEA | Original uploaded PDF |
| is_active | BOOLEAN | Current resume used for matching |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### jobs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| title | VARCHAR | |
| company | VARCHAR | |
| location | VARCHAR | |
| salary_min | INTEGER | Nullable |
| salary_max | INTEGER | Nullable |
| job_type | ENUM | full_time, part_time, contract, intern |
| seniority | ENUM | junior, mid, senior, lead, exec |
| visa_status | ENUM[] | Array; values: authorized, will_sponsor, citizen_only, not_specified |
| description | TEXT | Full job description |
| source_url | VARCHAR | Original listing URL |
| portal | ENUM | linkedin, indeed, glassdoor, wellfound, seek |
| external_id | VARCHAR | Portal-specific ID for dedup |
| scraped_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

**Unique constraint:** `(portal, external_id)`

### job_scores
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| job_id | UUID | FK → jobs.id |
| resume_id | UUID | FK → resumes.id |
| overall_score | INTEGER | 0–100 weighted sum |
| rubric_breakdown | JSONB | `{skills: 85, experience: 70, ...}` |
| reasoning | TEXT | 2-3 sentence LLM summary |
| scored_at | TIMESTAMPTZ | |

### applications
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| job_id | UUID | FK → jobs.id |
| tailored_resume_pdf | BYTEA | Generated PDF |
| tailored_content | JSONB | GPT-generated sections |
| status | ENUM | generated, applied, interview, rejected, offer |
| applied_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | For status changes |

### scrape_runs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| portal | ENUM | |
| status | ENUM | running, success, failed |
| jobs_found | INTEGER | |
| jobs_new | INTEGER | |
| error_message | TEXT | Nullable |
| started_at | TIMESTAMPTZ | |
| finished_at | TIMESTAMPTZ | |

### usage_logs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| operation | ENUM | match, resume_gen, parse |
| model | VARCHAR | e.g. "gpt-5.4" |
| tokens_input | INTEGER | |
| tokens_output | INTEGER | |
| cost_usd | DECIMAL(10,6) | |
| created_at | TIMESTAMPTZ | |

### settings
| Column | Type | Notes |
|--------|------|-------|
| key | VARCHAR | PK |
| value | JSONB | |
| updated_at | TIMESTAMPTZ | |

**Settings keys:** scrape_frequency, scrape_portals, match_threshold (default: 50), usage_cap_type, usage_cap_value, telegram_chat_id, search_keywords, preferred_locations, default_visa_filter

### Relationships
- resumes 1 ——  * job_scores
- jobs 1 —— * job_scores (one per resume version)
- jobs 1 —— 0..1 applications
- jobs.portal → scrape_runs.portal (logical, not FK)

## 4. LLM Scoring Rubric

LLM-based matching via LangChain + GPT 5.4 with a structured scoring rubric.

### Dimensions

| Dimension | Weight | Measures |
|-----------|--------|----------|
| Skills Match | 30% | Overlap between resume skills and JD requirements |
| Experience Fit | 25% | Years, seniority alignment, domain relevance |
| Role Alignment | 20% | Job title/responsibilities vs career trajectory |
| Education Match | 10% | Degree requirements vs qualifications |
| Location & Logistics | 10% | Remote/hybrid/onsite, timezone, relocation |
| Visa Compatibility | 5% | Job's visa_status vs user's authorization |

### Process

1. LLM receives parsed resume (structured + raw text) and full job description
2. Scores each dimension independently (0–100) with brief justification
3. Weighted sum produces `overall_score`
4. `rubric_breakdown` JSONB stores per-dimension scores
5. `reasoning` stores 2-3 sentence overall summary

### Threshold

Jobs scoring below `match_threshold` (default: 50) are stored but hidden from the dashboard by default. A "Show all" toggle reveals them.

## 5. Resume Generation & Apply Flow

### Flow

1. User clicks "Generate Resume & Apply" on a job card
2. Backend fetches job description + active resume from DB
3. **Usage cap check:** Query `usage_logs` against active cap → reject if exceeded
4. LangChain prompt sends resume + JD to GPT 5.4 with instructions to tailor content → returns JSON with: summary, experience bullets, skills to highlight, education emphasis
5. LaTeX template engine injects tailored content into template slots → `pdflatex` compiles → PDF
6. Response: PDF download link + tailored content preview + "Open Application Page" button
7. Application record created with status "generated"

### LaTeX Template Principles

- **ATS-first:** No multi-column layouts, no text boxes, no images — pure text flow
- **Sections:** Contact Info → Professional Summary → Experience → Skills → Education
- **Font:** Computer Modern or Latin Modern
- **Length:** Single page when possible, two pages max

### Usage Cap Enforcement

Before any GPT call, the backend:
1. Queries `usage_logs` for the active cap window (monthly/weekly/12-hourly)
2. Sums `cost_usd` (or `tokens_input + tokens_output`)
3. If >= cap value, returns error: "Usage cap reached, adjust in Settings"
4. Alert at 80% of cap shown in Settings dashboard

## 6. UI Design

### Design Tool

Google Stitch with installed skills:
- `stitch-design` — screen generation and editing
- `taste-design` — premium anti-generic aesthetics
- `enhance-prompt` — polishing design briefs
- `react-components` — converting Stitch output to production React/Next.js components
- `design-md` — design system documentation

### App Shell

Sidebar navigation (Dashboard, Applications, Resume, Settings) + top bar (logo, last scrape time, user avatar via Clerk).

### Pages

#### Dashboard (primary view)
- **Stats bar:** Total jobs, new today, avg match score, pending applications
- **Filter bar:** Location, salary range, job type, seniority, visa status, portal, score range
- **Sort controls:** Match score, date scraped, salary, company
- **Job list:** Card/table rows showing title, company, location, score badge, salary, visa tags, portal icon, date. Click to expand: full JD, rubric breakdown with per-dimension scores, "Generate Resume & Apply" button

#### Applications
- **Kanban pipeline:** Columns: Generated → Applied → Interview → Offer / Rejected
- **Application cards:** Job title, company, date applied, status, download tailored resume PDF
- **Quick actions:** Update status, re-download PDF, open portal link, view match reasoning

#### Resume
- **Upload zone:** Drag & drop PDF, shows parsed preview after upload
- **Parsed preview:** Skills tags, experience timeline, education cards — verify extraction accuracy
- **History:** Past uploads with timestamps, set any as active, re-score all jobs when switching

#### Settings
- **Scraping config:** Frequency (12h/daily/weekly), toggle portals on/off, search keywords, preferred locations
- **Matching config:** Score threshold (default: 50), default visa filter preset, rubric weight adjustments
- **GPT usage dashboard:** Tokens used (input/output), cost breakdown by operation, line chart over time
- **Usage caps:** Cap type (monthly/weekly/12-hourly), cap value (USD or tokens), current usage vs cap progress bar, alert at 80%
- **Notifications:** Telegram bot setup (chat ID), notification threshold, digest frequency

## 7. Project Structure

```
auto-job/
├── frontend/                    # Next.js (Vercel)
│   ├── src/
│   │   ├── app/                 # App router pages
│   │   │   ├── dashboard/
│   │   │   ├── applications/
│   │   │   ├── resume/
│   │   │   └── settings/
│   │   ├── components/          # React components (from Stitch)
│   │   ├── lib/                 # API client, utils
│   │   └── types/               # TypeScript interfaces
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── package.json
│
├── backend/                     # FastAPI (Railway)
│   ├── app/
│   │   ├── main.py              # Entrypoint + lifespan
│   │   ├── api/
│   │   │   ├── jobs.py
│   │   │   ├── resume.py
│   │   │   ├── apply.py
│   │   │   └── settings.py
│   │   ├── scrapers/
│   │   │   ├── base.py          # Abstract scraper interface
│   │   │   ├── linkedin.py
│   │   │   ├── indeed.py
│   │   │   ├── glassdoor.py
│   │   │   ├── wellfound.py
│   │   │   └── seek.py
│   │   ├── services/
│   │   │   ├── matcher.py       # LLM rubric scoring
│   │   │   ├── resume_parser.py # PDF → structured data
│   │   │   ├── resume_gen.py    # LangChain + LaTeX
│   │   │   ├── scheduler.py     # APScheduler config
│   │   │   ├── notifier.py      # Telegram bot
│   │   │   └── usage.py         # Token tracking + caps
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── templates/
│   │   │   └── resume.tex       # ATS-friendly LaTeX template
│   │   └── config.py            # Env vars, settings
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
│
├── .stitch/                     # Stitch design assets
├── docs/superpowers/specs/      # Design specs
└── .agents/skills/              # Installed Stitch skills
```

## 8. Key Dependencies

### Backend (Python)
- fastapi, uvicorn, asyncpg
- sqlalchemy[asyncio], alembic
- playwright
- langchain, langchain-openai
- pymupdf (PDF parsing)
- apscheduler
- python-telegram-bot
- pydantic

### Frontend (Node.js)
- next, react, react-dom
- tailwindcss
- @clerk/nextjs
- axios or fetch wrapper
- date-fns

### Infrastructure
- Clerk account (OAuth)
- OpenAI API key (GPT 5.4)
- Telegram bot token
- Railway account
- Vercel account
- pdflatex (texlive in Docker)

## 9. Verification Plan

1. **Backend API:** Start FastAPI locally, hit each endpoint with curl/httpie, verify responses match Pydantic schemas
2. **Scraper:** Run each portal scraper individually with test keywords, verify jobs are stored and deduplicated
3. **Matcher:** Score a sample job against a test resume, verify rubric_breakdown and overall_score are reasonable
4. **Resume gen:** Generate a tailored resume for a sample job, verify PDF output is valid and ATS-parseable
5. **Usage tracking:** Make several GPT calls, verify usage_logs are created and cap enforcement blocks when exceeded
6. **Frontend:** Run Next.js dev server, verify all 4 pages render, filters/sorts work, apply flow completes
7. **Notifications:** Configure test Telegram bot, trigger a scrape, verify digest message arrives
8. **E2E deploy:** Push frontend to Vercel, backend to Railway, verify cross-origin API calls work with Clerk auth
