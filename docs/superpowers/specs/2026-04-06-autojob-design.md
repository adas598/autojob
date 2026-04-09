# AutoJob — Design Specification (v2)

Personal job application automation tool that scrapes job portals, ranks listings against your resume, and generates tailored resumes and cover letters from templates.

## 1. Architecture

**Deployment:** Vercel (frontend) + Railway (backend + database)

- **Frontend:** Next.js + Tailwind CSS on Vercel free tier
- **Backend:** FastAPI monolith on Railway ($10-15/mo)
- **Database:** PostgreSQL on Railway
- **Auth:** Clerk OAuth

### Data Flow

1. **Scrape:** APScheduler triggers JobSpy (LinkedIn/Indeed/Glassdoor/Google Jobs) + Crawl4AI (Seek.com.au) -> raw jobs stored in PostgreSQL
2. **Score:** New jobs -> LLM rubric scores each against active resume -> score + reasoning saved
3. **Rank:** Top-K jobs (K configurable) shown on dashboard, sorted by relevance score
4. **Apply:** User picks job -> Gemma 4 31B fills resume + cover letter templates via docxtpl -> DOCX/PDF output -> user applies manually

### Backend Components

| Component | Tech | Purpose |
|-----------|------|---------|
| API server | FastAPI (async) | REST endpoints for frontend |
| Scheduler | APScheduler | Configurable cron: 12h / daily / weekly |
| Scraper (multi-portal) | JobSpy | LinkedIn, Indeed, Glassdoor, Google Jobs |
| Scraper (Seek) | Crawl4AI + CSS extraction | Seek.com.au with matching schema |
| LLM abstraction | LangChain + Google AI Studio | Gemma 4 31B for scoring + template filling |
| Resume parser | PyMuPDF | PDF text + structured extraction |
| Template engine | docxtpl (Jinja2 in DOCX) | Fills resume + cover letter templates |
| PDF converter | docx2pdf / LibreOffice headless | DOCX -> PDF conversion |
| ORM | SQLAlchemy (async) + Alembic | Models + migrations via asyncpg |

### LLM Strategy

- **Model:** Gemma 4 31B via Google AI Studio (free tier)
- **Abstraction:** LangChain `ChatGoogleGenerativeAI` with provider swappability
- **Swappable to:** OpenRouter, Ollama Cloud, DeepSeek, Claude Haiku — via `LLM_PROVIDER` env var
- **Usage:** Template filling (structured JSON output), job scoring (rubric evaluation)
- **NOT used for:** Creative composition. LLM only fills pre-designed template placeholders.

## 2. Job Portals

### JobSpy (primary — LinkedIn, Indeed, Glassdoor, Google Jobs)

Open-source library (`python-jobspy`) that scrapes multiple job boards concurrently:
- Supported: LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter
- Returns: title, company, location, salary, job_type, description, job_url, date_posted
- Limitations: ~1,000 results per search per platform, rate-limited on LinkedIn after page 10

### Crawl4AI (Seek.com.au only)

Crawl4AI with `JsonCssExtractionStrategy` for structured extraction:
- CSS selectors for job listing cards on search results
- Individual page crawl for full JD
- Stealth mode enabled, 2-3 second delays between requests
- Output mapped to same `ScraperResult` schema as JobSpy

### Common Scraper Interface

All scrapers output the same `ScraperResult` dataclass:
```python
@dataclass
class ScraperResult:
    title: str
    company: str
    location: str
    salary_min: int | None
    salary_max: int | None
    job_type: str | None
    seniority: str | None
    visa_info: str | None
    description: str
    source_url: str
    portal: str              # linkedin, indeed, glassdoor, google_jobs, seek
    external_id: str
    date_posted: datetime | None
    scraped_via: str         # jobspy or crawl4ai
```

**Dedup:** Jobs are deduplicated on `(portal, external_id)` unique constraint.

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
| visa_info | VARCHAR | Free text from scrape (varies per portal) |
| description | TEXT | Full job description |
| source_url | VARCHAR | Original listing URL |
| portal | ENUM | linkedin, indeed, glassdoor, google_jobs, seek |
| external_id | VARCHAR | Portal-specific ID for dedup |
| scraped_via | ENUM | jobspy, crawl4ai |
| scraped_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

**Unique constraint:** `(portal, external_id)`

### job_scores
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| job_id | UUID | FK -> jobs.id |
| resume_id | UUID | FK -> resumes.id |
| overall_score | INTEGER | 0-100 weighted sum |
| rubric_breakdown | JSONB | `{skills: 85, experience: 70, ...}` |
| reasoning | TEXT | 2-3 sentence LLM summary |
| scored_at | TIMESTAMPTZ | |

### applications
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| job_id | UUID | FK -> jobs.id |
| tailored_resume_pdf | BYTEA | Generated PDF |
| tailored_resume_docx | BYTEA | Generated DOCX |
| tailored_content | JSONB | LLM-generated sections |
| cover_letter_pdf | BYTEA | Generated cover letter PDF |
| cover_letter_docx | BYTEA | Generated cover letter DOCX |
| cover_letter_content | JSONB | LLM-generated cover letter sections |
| template_used | VARCHAR | Template name used |
| status | ENUM | generated, applied, interview, rejected, offer |
| applied_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | For status changes |

### scrape_runs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| portal | ENUM | |
| scraped_via | ENUM | jobspy, crawl4ai |
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
| operation | ENUM | score, resume_gen, cover_letter_gen, parse |
| model | VARCHAR | e.g. "gemma-4-31b" |
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

**Settings keys:** scrape_frequency, scrape_portals, match_threshold (default: 50), top_k (default: 50), usage_cap_type, usage_cap_value, search_keywords, preferred_locations, default_visa_filter

### Relationships
- resumes 1 -- * job_scores
- jobs 1 -- * job_scores (one per resume version)
- jobs 1 -- 0..1 applications
- jobs.portal -> scrape_runs.portal (logical, not FK)

## 4. LLM Scoring Rubric

LLM-based matching via LangChain + Gemma 4 31B with a structured scoring rubric.

### Dimensions

| Dimension | Weight | Measures |
|-----------|--------|----------|
| Skills Match | 30% | Overlap between resume skills and JD requirements |
| Experience Fit | 25% | Years, seniority alignment, domain relevance |
| Role Alignment | 20% | Job title/responsibilities vs career trajectory |
| Education Match | 10% | Degree requirements vs qualifications |
| Location & Logistics | 10% | Remote/hybrid/onsite, timezone, relocation |
| Visa Compatibility | 5% | Job's visa info vs user's authorization |

### Process

1. LLM receives parsed resume (structured + raw text) and full job description
2. Scores each dimension independently (0-100) with brief justification
3. Weighted sum produces `overall_score`
4. `rubric_breakdown` JSONB stores per-dimension scores
5. `reasoning` stores 2-3 sentence overall summary

### Threshold & Top-K

Jobs scoring below `match_threshold` (default: 50) are stored but hidden from the dashboard by default. A "Show all" toggle reveals them. Dashboard shows top `top_k` (default: 50) jobs sorted by score.

## 5. Resume & Cover Letter Generation

### Template System

**Engine:** docxtpl (Jinja2 templating for DOCX files)

**Templates:**
- `resume_classic.docx` — Traditional, blue header, single column
- `resume_modern.docx` — Minimal, clean typography
- `cover_letter.docx` — Professional letter format

**ATS Safety Rules:**
- Single column layout only
- No tables for content (ok for header layout)
- Standard fonts: Calibri, Arial
- Bullet points as plain text (- or *)
- No images/graphics

### LLM Input/Output Contract

**Input to LLM:**
```json
{
  "job_title": "string",
  "company": "string",
  "job_description": "string",
  "parsed_resume": {
    "skills": ["string"],
    "experience": [{"title": "string", "company": "string", "dates": "string", "bullets": ["string"]}],
    "education": [{"degree": "string", "institution": "string", "year": "string"}],
    "summary": "string"
  }
}
```

**Output from LLM (fills template placeholders):**
```json
{
  "tailored_summary": "string",
  "tailored_experience": [{"title": "string", "company": "string", "dates": "string", "bullets": ["string"]}],
  "skills_to_highlight": ["string"],
  "education_emphasis": "string",
  "cover_letter_paragraphs": {
    "opening": "string",
    "body": "string",
    "closing": "string"
  }
}
```

### Apply Flow

1. User clicks "Generate Resume & Apply" on a job card
2. Backend fetches job description + active resume from DB
3. **Usage cap check:** Query `usage_logs` against active cap -> reject if exceeded
4. LangChain sends resume + JD to Gemma 4 31B -> returns JSON with tailored content
5. docxtpl fills template with LLM output -> DOCX generated
6. DOCX converted to PDF via docx2pdf / LibreOffice headless
7. Response: DOCX + PDF download links + tailored content preview
8. Application record created with status "generated"
9. User selects format (DOCX or PDF) based on job provider requirements

### Usage Cap Enforcement

Before any LLM call, the backend:
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
- **Filter bar:** Location, salary range, job type, seniority, portal, score range
- **Sort controls:** Match score, date scraped, salary, company
- **Job list:** Card/table rows showing title, company, location, score badge, salary, visa tags, portal icon, date. Click to expand: full JD, rubric breakdown with per-dimension scores, "Generate Resume & Apply" button

#### Applications
- **Kanban pipeline:** Columns: Generated -> Applied -> Interview -> Offer / Rejected
- **Application cards:** Job title, company, date applied, status, download tailored resume (DOCX/PDF), download cover letter (DOCX/PDF)
- **Quick actions:** Update status, re-download documents, open portal link, view match reasoning

#### Resume
- **Upload zone:** Drag & drop PDF, shows parsed preview after upload
- **Parsed preview:** Skills tags, experience timeline, education cards — verify extraction accuracy
- **History:** Past uploads with timestamps, set any as active, re-score all jobs when switching

#### Settings
- **Scraping config:** Frequency (12h/daily/weekly), toggle portals on/off, search keywords, preferred locations, top-K count
- **Matching config:** Score threshold (default: 50), rubric weight adjustments
- **LLM config:** Provider selection, model name, API key
- **Usage dashboard:** Tokens used (input/output), cost breakdown by operation, line chart over time
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
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── database.py          # Async engine + session
│   │   ├── api/
│   │   │   ├── jobs.py
│   │   │   ├── resume.py
│   │   │   ├── apply.py
│   │   │   ├── scrape.py
│   │   │   └── settings.py
│   │   ├── scrapers/
│   │   │   ├── base.py          # ScraperResult + abstract interface
│   │   │   ├── jobspy_scraper.py # JobSpy wrapper
│   │   │   └── seek_scraper.py  # Crawl4AI for Seek.com.au
│   │   ├── services/
│   │   │   ├── llm.py           # LangChain abstraction layer
│   │   │   ├── scorer.py        # LLM rubric scoring
│   │   │   ├── resume_parser.py # PDF -> structured data
│   │   │   ├── resume_gen.py    # docxtpl template filling
│   │   │   └── cover_letter.py  # Cover letter generation
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── templates/
│   │   │   ├── resume_classic.docx
│   │   │   ├── resume_modern.docx
│   │   │   └── cover_letter.docx
│   │   └── scheduler.py         # APScheduler config
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
│
├── contracts/                   # Shared schemas & API spec
│   ├── db-schema.sql
│   ├── openapi.yaml
│   └── llm-schemas.json
│
├── docs/superpowers/specs/      # Design specs
└── design-artifacts/            # Stitch design assets
```

## 8. Key Dependencies

### Backend (Python)
- fastapi, uvicorn, asyncpg
- sqlalchemy[asyncio], alembic
- python-jobspy (multi-portal scraping)
- crawl4ai (Seek.com.au scraping)
- langchain, langchain-google-genai
- pymupdf (PDF parsing)
- docxtpl, python-docx (template filling)
- docx2pdf (DOCX -> PDF conversion)
- apscheduler
- pydantic

### Frontend (Node.js)
- next, react, react-dom
- tailwindcss
- @clerk/nextjs
- axios or fetch wrapper
- date-fns

### Infrastructure
- Clerk account (OAuth)
- Google AI Studio API key (Gemma 4 31B)
- Railway account
- Vercel account

## 9. Development Tracks

### Track A: Data Pipeline (Ayush)
A1. Project scaffold + database models + CRUD APIs
A2. JobSpy integration (LinkedIn, Indeed, Glassdoor, Google Jobs)
A3. Crawl4AI Seek.com.au scraper
A4. APScheduler cron jobs
A5. Job scoring/ranking (uses LLM layer from Track B)
A6. Docker + Railway deploy

### Track B: Documents & UI (Aneet)
B1. LangChain LLM abstraction layer (FIRST deliverable — unblocks A5)
B2. Resume parser (PyMuPDF + LLM structuring)
B3. docxtpl template system (resume + cover letter, DOCX + PDF)
B4. Application tracking API
B5. Next.js frontend dashboard

### Integration Points
1. B1 (LLM layer) must ship before A5 (scorer)
2. A1 (DB schema) must ship before B2/B3/B4
3. API spec agreed upfront via contracts/openapi.yaml

## 10. Verification Plan

1. **Backend API:** Start FastAPI locally, hit each endpoint with curl/httpie, verify responses match Pydantic schemas
2. **Scraper:** Run JobSpy with test keywords, verify jobs stored and deduplicated. Run Seek scraper, verify matching schema.
3. **Scorer:** Score a sample job against a test resume, verify rubric_breakdown and overall_score
4. **Resume gen:** Generate a tailored resume for a sample job, verify DOCX + PDF output with placeholders filled
5. **Cover letter:** Generate a cover letter, verify content matches job
6. **Top-K:** Set threshold + K, verify dashboard shows correct subset
7. **Usage tracking:** Make several LLM calls, verify usage_logs and cap enforcement
8. **Frontend:** Run Next.js dev server, verify all 4 pages render, filters/sorts work, apply flow completes
9. **E2E deploy:** Push frontend to Vercel, backend to Railway, verify cross-origin API calls work with Clerk auth
