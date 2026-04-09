---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete]
inputDocuments:
  - docs/superpowers/specs/2026-04-06-autojob-design.md
  - docs/superpowers/plans/2026-04-06-autojob-plan1-backend-core.md
  - contracts/db-schema.sql
  - contracts/openapi.yaml
  - contracts/llm-schemas.json
workflowType: 'prd'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 5
classification:
  projectType: web_app
  domain: general
  complexity: medium
  projectContext: brownfield
---

# Product Requirements Document - auto-job

**Author:** Sir
**Date:** 2026-04-09

## Executive Summary

Job hunting under visa and financial pressure is a full-time job on top of your full-time job search. Every day, hundreds of relevant roles are posted across LinkedIn, Indeed, Glassdoor, and Seek — but finding them, evaluating fit, and tailoring a resume for each takes hours of repetitive manual work. Opportunities slip by while you're preparing applications for yesterday's listings.

AutoJob eliminates both bottlenecks. It scrapes job boards via JSearch API (pay-as-you-go, $0.005/request), enriches listings with Crawl4AI for full job descriptions and visa details, scores each opportunity against the user's resume using a 6-dimension LLM rubric (Gemma 4 31B), and generates submission-ready resumes and cover letters from pre-designed templates — turning a discovered job into a ready-to-submit application in under 60 seconds.

The system is built for two users (Ayush and Aneet) under time pressure: upload a "mother" resume, configure search preferences, and the pipeline runs on a configurable cron schedule per user. The dashboard surfaces the top-K most relevant jobs, tracks application status from generation through interview outcome, and provides full visibility into scrape health and cost. Designed for minimal operating cost (under $30/month for two users) with a two-developer parallel build optimized for speed to first usable milestone.

### What Makes This Special

1. **Last-mile automation.** Most job tools stop at discovery. AutoJob's core value is the final step: LLM-tailored resume and cover letter generation from templates, output in both DOCX and PDF. The document generation *is* the product.
2. **Human-in-the-loop.** No mass-apply. Every application is reviewed and submitted by the user. Avoids account flagging, maintains quality, keeps the user in control.
3. **Visa-aware filtering.** First-class sponsorship status filtering — critical for visa holders who waste hours applying to roles that won't sponsor.
4. **Resilient two-layer scraping.** JSearch API for reliable structured discovery (burst-friendly at 5 req/sec). Crawl4AI for enrichment and Seek.com.au coverage. Partial failures don't block the pipeline.
5. **Fast first value.** Scored matches within 5 minutes of resume upload. Raw jobs appear immediately, scores populate progressively.
6. **Incremental delivery.** Each development milestone is independently useful. The user benefits before the full system is complete.
7. **Cost-controlled by design.** Rate limiting across all layers: burst for JSearch, paced for Crawl4AI, queued for LLM, with per-user configurable spend caps and per-operation cost tracking.

## Project Classification

- **Type:** Web application (SPA dashboard + REST API backend + automated data pipeline)
- **Domain:** General / productivity automation
- **Complexity:** Medium — multi-source scraping, LLM orchestration, document generation pipeline, scheduled background jobs, two-track parallel development
- **Context:** Brownfield — design specification, database schema, API contracts, and backend scaffold already exist

## Success Criteria

### User Success

- System surfaces relevant jobs the user would have missed manually across LinkedIn, Indeed, Glassdoor, Google Jobs, and Seek
- User agrees with the LLM's top-10 ranked jobs at least 80% of the time (manual validation, week 1)
- Application throughput: 30-70 tailored applications per week — up from ~5-10 manually
- Time per application: under 60 seconds from "view scored job" to "download tailored resume + cover letter"
- Dashboard supports rapid triage: scan, select, generate, download cycle under 5 minutes for 15 applications
- First value moment: scored job list visible within 5 minutes of uploading resume
- Zero time wasted reviewing jobs that won't sponsor (visa filtering)

### Business Success

- 3-month outcome: at least one job offer from AutoJob-generated applications
- Consistent application volume of 30+ per week without manual intervention beyond selecting jobs and clicking generate
- Total operating cost under $30/month for two users
- Scraping pipeline runs reliably on schedule with <5% failure rate across portals
- Track response rate per portal/score range to identify highest-yield channels

### Technical Success

- JSearch API calls succeed >99% of the time; Crawl4AI enrichment succeeds >90%
- Generated resumes and cover letters require no manual editing in >80% of cases
- LLM output JSON validated against schema before template filling — reject and retry on malformed output (max 2 retries)
- Zero documents generated with unfilled `{{ placeholder }}` tags — validated before storage
- DOCX + PDF generation completes in <5 seconds per application
- Bulk generation of 10 applications completes in <60 seconds
- All new jobs from a scrape run scored within 15 minutes
- Zero duplicate jobs stored; dedup on (user_id, portal, external_id) works consistently
- Template-to-LLM-schema contract validation passes in CI
- Templates are code-generated ensuring ATS compliance by construction
- Template creation takes <1 hour per variant using Claude Code skills
- Database storage stays under 500MB for first 3 months at 70 applications/week

### Delivery Success

- Day 1 = first day of parallel development after contracts are agreed and repo is set up
- B1 (LLM abstraction layer) delivered and usable by Day 2 — both tracks unblocked
- Each development milestone is independently testable and demonstrable

### Measurable Outcomes

| Metric | Target | Measured By |
|--------|--------|-------------|
| Applications/week | 30-70 | `applications` table count |
| Triage-to-download cycle | <5 min for 15 apps | Manual validation |
| Time to first scored list | <5 minutes | Manual validation |
| Cost/month (2 users) | <$30 | `usage_logs` + JSearch billing + Railway |
| Scrape success rate | >95% | `scrape_runs` success/total |
| Template/schema drift | 0 | CI test |
| Response rate | Track per portal | `applications` status != no_response / total |
| Interview conversion | Track over 3 months | `applications` status = interview |
| Job offer | >=1 in 3 months | `applications` status = offer |

## Product Scope

See **Project Scoping & Phased Development** below for the comprehensive MVP feature set, growth features, vision, and risk mitigation strategy with track assignments.

## User Journeys

### Journey 1: The Daily Triage — Monday Morning Bulk Apply

**Persona:** Ayush, software engineer on a visa, financially stressed, needs to apply to 10+ jobs daily without burning out.

**Opening Scene:** 7:30 AM Monday. Ayush slept while AutoJob scraped overnight. He opens the dashboard — no five browser tabs, no hour of scrolling. A clean, score-sorted list. Top bar shows a green dot: all portals scraped successfully.

**Rising Action:** 87 new jobs, already scored. Top 15 are green (80+). He scans titles and companies. A senior backend role at a company he's never heard of is ranked #3 at 91%. He clicks it — side panel shows the full JD, rubric breakdown: skills 95%, experience 88%, visa compatibility 100%. "They sponsor."

**Climax:** He clicks "Select all above 80", checks off 12 jobs. Hits "Bulk Generate." Progress bar: 3/12... 7/12... 12/12. Done in 40 seconds. Downloads the zip: `AutoJob_2026-04-14_12-applications.zip` — 12 tailored resumes + 12 cover letters. Opens one — summary is tailored to the JD, experience bullets emphasize the right stack. No edits needed.

**Resolution:** By 8:15 AM, 12 applications submitted. He marks each "applied" in the dashboard. Yesterday's applications show one moved to "interview." He closes the laptop. The system scrapes again tonight.

---

### Journey 2: First Time Setup — Resume Drives Everything

**Persona:** Ayush, day one. Just deployed AutoJob. Has his "mother" resume PDF ready.

**Opening Scene:** Fresh dashboard. Empty — just an upload zone: "Upload your resume to get started."

**Rising Action:** He drags in his resume PDF. Hits "Parse Resume." The system extracts text, skills, experience, education. Parsed preview appears: skills tags (Python, FastAPI, AWS, Docker...), experience timeline, education cards. He notices the parser missed "Kubernetes" from a two-column section — clicks "Edit parsed data", adds it manually, saves.

The system then suggests search roles based on his resume: "Backend Engineer, Software Engineer, DevOps Engineer, Platform Engineer." Displayed as editable tags. He adds "Data Engineer", removes "DevOps Engineer."

Next prompt: "Where are you open to working?" He types "Sydney, Melbourne, Remote."

**Climax:** He clicks "Start First Scrape." JSearch fires for all role keywords across four portals, Crawl4AI hits Seek. Progress: "LinkedIn... 47 jobs. Indeed... 63 jobs." Within 2 minutes, 180 jobs in the database. Scoring begins — green badges appear progressively. Within 5 minutes, his first ranked job list.

**Resolution:** Top job: 94% match — a backend role at a fintech in Sydney that sponsors visas. He never would have found it on page 3 of Seek. Generates a resume, downloads it, submits his first application. The system is configured — tomorrow morning, new jobs will be waiting.

---

### Journey 3: The Garbage Results Morning — Error Recovery

**Persona:** Ayush, two weeks in. System has been running smoothly.

**Opening Scene:** Wednesday morning. Dashboard top bar shows an amber dot — partial scrape failure. He sees 12 new jobs instead of the usual 50-80. Top score is 43%.

**Rising Action:** He checks scrape runs. LinkedIn: success, 8 jobs. Indeed: **failed** — "429 Too Many Requests." Google Jobs: **failed** — "timeout." Seek: success, 0 new postings. Circuit breaker kicked in and logged the errors.

**Climax:** He hits "Trigger Manual Scrape" — selects Indeed and Google Jobs only. Re-runs succeed: 52 new jobs. Scoring begins. Within 5 minutes, 8 jobs score above 80%. System self-healed with one click.

**Resolution:** He adjusts search keywords in Settings — adds "platform engineer." Checks scrape history: Indeed throttles on Tuesdays. Notes to monitor. The `last_successful_scrape_at` timestamp ensures next automatic scrape covers the gap window — no silent data loss.

---

### Journey 4: Admin Mode — Cost & Configuration Review

**Persona:** Ayush, end of month. Reviewing system health and costs.

**Opening Scene:** Opens Settings → Usage Dashboard.

**Rising Action:** JSearch API: $2.85 this month (570 requests). LLM: $0 (free tier). Total: $22.85 including $20 Railway. Well under $30 budget.

Application stats: 247 this month. 18 responses (7.3% response rate). 4 interviews. Indeed has 11% response rate, LinkedIn 3%. Seek produced 2 of 4 interviews despite fewer total applications.

**Climax:** He tunes the system: bumps match threshold from 50 to 65 (less noise), changes scrape frequency from 12h to daily (sufficient volume), enables default visa filter (hide non-sponsoring roles).

**Resolution:** Next month will be more focused — fewer but higher-quality matches, same cost. Per-user usage cap at $10/month, well within margin. System is self-sustaining and improving.

---

### Journey Requirements Summary

| Journey | Key Capabilities Revealed |
|---------|--------------------------|
| Daily Triage | Score-sorted dashboard, bulk select/generate, zip download, side panel quick-view, status tracking |
| First Time Setup | Resume parse + preview + edit, LLM role suggestion (`suggested_roles`), location input, manual scrape trigger, onboarding flow |
| Error Recovery | Scrape health indicator (top bar green/amber/red), per-portal re-trigger, circuit breaker transparency, keyword editing, gap-aware incremental scraping |
| Admin/Config | Usage dashboard (cost by component), application analytics (response rate by portal), settings tunability, scrape health history |

**New MVP requirements surfaced from journeys:**
- `suggested_roles: string[]` in resume parser LLM output (Track B, 30 min)
- `PUT /resume/{id}/parsed` endpoint for editing parsed data (Track B, 1-2 hours)
- Scrape health status indicator in dashboard top bar (Track B, 30 min)
- Editable role keyword tags in onboarding flow (Track B)

## Web Application Specific Requirements

### Project-Type Overview

AutoJob is a Next.js SPA (App Router) backed by a FastAPI REST API. Two-user authenticated dashboard (Ayush and Aneet) with fully independent configurations, data, and scraping schedules. Shared infrastructure only. Core interaction: triage-and-act — scan jobs, select, generate documents, download, apply externally.

### User Model

- **Users:** 2 (Ayush, Aneet) — proper account separation, not multi-tenant SaaS
- **Auth:** Clerk OAuth with separate accounts and sessions
- **Data isolation:** All data scoped by `user_id` — resumes, jobs, job_scores, applications, settings, scrape_runs, usage_logs
- **Scoping enforcement:** Middleware-based user_id injection (one place to enforce, not per-query WHERE clauses)
- **Independent configs:** Each user owns their scrape frequency, keywords, locations, portals, thresholds, usage caps
- **Independent scraping:** Each user's cron job runs on their own schedule with their own keywords
- **Shared infrastructure:** Same Railway backend ($20/mo plan), same PostgreSQL, same API server

### Database Impact

Add `user_id UUID NOT NULL` to all tables:
- `jobs` — per-user dedup: unique on `(user_id, portal, external_id)`
- `settings` — composite PK: `(user_id, key)`
- `resumes`, `job_scores`, `applications`, `scrape_runs`, `usage_logs` — filtered by user_id
- No Clerk users table in PostgreSQL — `user_id` is a UUID string from Clerk token
- Admin escape hatch: unscoped queries available for system-wide usage aggregation

### Technical Architecture

**Frontend:**
- Next.js 14+ with App Router, Tailwind CSS
- Clerk authentication with login/signup flow
- All API calls include auth token, backend extracts `user_id` from Clerk session
- React state + context for client-side state (no Redux needed)

**Browser Support:** Chrome and Firefox (latest 2 versions). Desktop-first.

**Performance Targets:**
- Dashboard load: <2 seconds
- Job detail panel: <500ms
- Bulk generate: progress indicator, non-blocking
- API reads: <200ms, document generation: <5s

**SEO:** None. Authenticated dashboard.

**Accessibility:** Semantic HTML, keyboard-navigable. No formal WCAG audit.

**Scheduler:**
- APScheduler runs per-user cron jobs — reads each user's `scrape_frequency` from settings
- JSearch calls can overlap between users (fast HTTP)
- Crawl4AI enrichment can run concurrently ($20 Railway plan has sufficient memory)

**Deployment:**
- Frontend: Vercel (free tier)
- Backend: Railway ($20/mo plan)
- Database: Railway PostgreSQL addon
- Clerk: free tier (2 users well within 10,000 MAU limit)

**Cost Model (2 users):**

| Component | Monthly |
|-----------|---------|
| Railway ($20 plan) | $20 |
| JSearch API (2 users) | $4-6 |
| Google AI Studio | $0 |
| **Total** | **~$24-26** |

Budget target: under $30/month for two users.

### Testing Requirements

**User isolation tests (mandatory MVP):**
- User A cannot see User B's jobs, resumes, applications, or settings
- User A's scrape run does not affect User B's data
- Deleting User A's resume does not cascade to User B
- Auth token required on all endpoints — 401 without it

**Skipped (not applicable):** Native app, CLI, offline mode, PWA, mobile-first

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP — the minimum that lets two users (Ayush and Aneet) start applying to 30-70 jobs/week with tailored documents. Speed to first usable milestone is the governing constraint. Each milestone delivers standalone value — the user benefits before the full system is complete.

**Resource Requirements:** 2 developers, parallel tracks, ~2 weeks to MVP.
- **Track A (Ayush):** Data pipeline — scraping, scheduling, scoring, infrastructure
- **Track B (Aneet):** Document generation, LLM integration, templates, frontend

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
1. Daily Triage — scan scored jobs, bulk select, generate, download, apply
2. First Time Setup — upload resume, parse, suggest roles, configure, first scrape
3. Error Recovery — view scrape failures, manual re-trigger, keyword adjustment
4. Admin/Config — review costs, adjust thresholds, monitor health

**Must-Have Capabilities:**

| Capability | Track | Notes |
|------------|-------|-------|
| Resume upload, parse, edit, LLM role suggestion | B | Onboarding flow entry point |
| JSearch API scraping (4 portals) | A | Pay-as-you-go $0.005/req |
| Crawl4AI enrichment + Seek.com.au | A | Full JD, visa info, CSS extraction |
| Incremental scraping (`last_successful_scrape_at`) | A | No silent data gaps |
| LLM scoring (6-dimension rubric), top-K ranking | A | Depends on B1 (LLM layer) |
| LLM abstraction layer (LangChain + Gemma 4 31B) | B | **FIRST DELIVERABLE — Day 2** |
| LLM service stub for parallel development | A | Unblocks scoring before B1 ships |
| docxtpl template filling (resume + cover letter) | B | DOCX primary, lazy PDF conversion |
| Template generation script (contract-bound) | B | Claude Code + python-docx |
| LLM output validation + retry (max 2) | B | JSON schema check before filling |
| Zero unfilled placeholder validation | B | Checked before document storage |
| Bulk generate + zip download | B | Essential for 30-70/week target |
| Application tracking (6 statuses) | B | generated/applied/interview/rejected/offer/no_response |
| Per-user auth (Clerk OAuth) | Shared | 2 users, independent data |
| Middleware-based user_id scoping | Shared | One place to enforce, not per-query |
| Configurable cron scheduling | A | Per-user frequency (12h/daily/weekly) |
| Rate limiting (all layers) | A | JSearch burst, Crawl4AI pace, LLM queue, circuit breakers |
| Usage tracking + per-user cost caps | Shared | Warning at 80%, hard stop at 100% |
| Dashboard (score colors, bulk select, side panel, scrape health) | B | Rapid triage UX |
| Template validation tests | B | Placeholder/schema CI check |
| User isolation tests | Shared | Mandatory — no data leakage |
| Docker + Railway deploy | A | $20/mo Railway plan |

### Post-MVP Features

**Phase 2 (Growth):**
- Custom template generation via Claude Code (user-requested layouts)
- Template A/B performance tracking (which style gets interviews)
- Email/Telegram notifications for high-scoring new jobs
- Rubric weight customization per user preference
- S3-compatible object storage migration for document binaries
- Application analytics (conversion rates by portal, score range, template)
- Scrape health dashboard with per-portal detailed status
- Auto-set `no_response` status after N days (configurable)

**Phase 3 (Vision):**
- Learning from feedback: "not relevant" signals refine scoring rubric
- Multi-user SaaS support (beyond 2 users, billing, onboarding)
- Browser extension: one-click apply directly on job board pages
- Interview prep: LLM generates company-specific talking points from JD + resume
- Resume version control: track which version performed best

### Risk Mitigation Strategy

| Risk | Impact | Mitigation |
|------|--------|------------|
| B1 (LLM layer) delivery delay | Blocks both tracks | LLM stub on Day 1 (Track A) |
| JSearch API changes/downtime | No new jobs scraped | Circuit breaker + manual re-trigger + `last_successful_scrape_at` gap recovery |
| Crawl4AI Seek breakage | Lose one portal | Other 4 portals via JSearch unaffected |
| LLM returns malformed output | Broken documents | JSON validation against schema + retry (max 2) + unfilled placeholder check |
| User data leakage between accounts | Privacy breach | Middleware-based user_id scoping + isolation tests in CI |
| Railway resource limits | Service degrades | $20/mo plan provides headroom; sequential Crawl4AI if needed |
| Resume parsing produces garbage | Bad scores cascade downstream | Editable parsed data — user corrects before scoring |
| Scraper rate-limited/blocked | Incomplete job data | Exponential backoff, circuit breaker at 5 failures, per-portal disable + log |

## Functional Requirements

### Resume Management

- FR1: User can upload a PDF resume and trigger parsing
- FR2: System can extract text, skills, experience, and education from a PDF resume
- FR3: System can suggest relevant job title keywords based on parsed resume content
- FR4: User can view a parsed preview of their uploaded resume (skills tags, experience, education)
- FR5: User can edit parsed resume data (skills, experience, education) to correct extraction errors
- FR6: User can set a resume as active for scoring and document generation
- FR7: User can view upload history and switch active resume
- FR8: System re-scores all unscored jobs when the active resume changes

### Job Discovery & Scraping

- FR9: System can scrape job listings from LinkedIn, Indeed, Glassdoor, and Google Jobs via JSearch API
- FR10: System can scrape job listings from Seek.com.au via Crawl4AI with CSS extraction
- FR11: System can enrich JSearch results with full job descriptions and visa information via Crawl4AI
- FR12: System can deduplicate jobs per user on portal and external ID
- FR13: System can run scraping on a configurable schedule (12-hourly, daily, weekly) per user
- FR14: System can anchor incremental scraping to last successful scrape timestamp per portal, preventing data gaps
- FR15: User can manually trigger a scrape run for selected portals
- FR16: User can configure search keywords, preferred locations, and enabled portals
- FR17: System can detect repeated scrape failures and temporarily disable affected portals
- FR18: User can view scrape run history with per-portal status and error details

### Job Scoring & Ranking

- FR19: System can score each job against the active resume using a 6-dimension LLM rubric (skills, experience, role, education, location, visa)
- FR20: System can compute an overall weighted score (0-100) and store per-dimension breakdown
- FR21: System can queue scoring as a background process, populating scores progressively
- FR22: User can view jobs sorted by score (highest first) with color-coded badges (green 80+, yellow 60-79, red <60)
- FR23: User can filter jobs by portal, job type, seniority, location, salary range, minimum score, and visa info
- FR24: User can configure match threshold and top-K count to control dashboard visibility
- FR25: User can expand a job to view full description, rubric breakdown, and scoring reasoning

### Document Generation

- FR26: System can generate a tailored resume by filling a docxtpl template with LLM-produced content
- FR27: System can generate a tailored cover letter by filling a docxtpl template with LLM-produced content
- FR28: System can validate LLM output against schema before template filling and retry on failure
- FR29: System can verify zero unfilled placeholders exist before storing generated documents
- FR30: System can produce documents in DOCX format, with PDF conversion on demand
- FR31: User can select which template to use for generation
- FR32: User can bulk-select multiple jobs and generate all applications in one action
- FR33: User can download bulk-generated documents as a zip file with clear naming (CompanyName_JobTitle_format)
- FR34: User can download individual resume or cover letter in DOCX or PDF format

### Application Tracking

- FR35: System can create an application record when documents are generated for a job
- FR36: User can view all applications with status filter
- FR37: User can update application status (generated, applied, interview, rejected, offer, no_response)
- FR38: User can view application statistics: counts by status, response rate by portal
- FR39: User can re-download generated documents for any application

### Configuration & Cost Control

- FR40: User can configure scrape frequency, keywords, locations, portals, and match threshold
- FR41: User can set a usage cost cap (monthly, weekly, or 12-hourly) with a USD value
- FR42: System can track LLM and API usage per operation (score, resume_gen, cover_letter_gen, parse) with token counts and cost
- FR43: System can warn user at 80% of usage cap and reject LLM calls at 100%
- FR44: User can view usage dashboard: cost breakdown by component, tokens used, cost by operation
- FR45: User can view JSearch API usage (requests this month, estimated cost) alongside LLM usage

### Authentication & User Isolation

- FR46: User can sign up and log in via Clerk OAuth
- FR47: System can scope all data access to the authenticated user via middleware
- FR48: User cannot view, modify, or affect another user's data (resumes, jobs, scores, applications, settings)
- FR49: All API endpoints require authentication and return 401 without valid token

### Dashboard & System Health

- FR50: User can view a dashboard with score-sorted job list, stats bar, and filter controls
- FR51: User can view scrape health indicator in top bar (green/amber/red based on last run status)
- FR52: User can navigate between Dashboard, Applications, Resume, and Settings pages
- FR53: User can view a job detail in a side panel without navigating away from the list
- FR54: User can select all jobs above a configurable score threshold with one click

### Onboarding & Templates

- FR55: System can guide first-time users through onboarding: resume upload, parse preview, role suggestion, location selection, and first scrape trigger
- FR56: User can view real-time progress of an active scrape run (jobs found per portal)
- FR57: User can view available resume and cover letter templates

## Non-Functional Requirements

### Performance

- NFR1: Dashboard job list loads within 2 seconds for up to 500 jobs (paginated, 20 per page)
- NFR2: Job detail side panel renders within 500ms (data pre-fetched with list)
- NFR3: Single document generation (LLM call + template fill + DOCX output) completes within 5 seconds
- NFR4: Bulk generation of 10 applications completes within 60 seconds
- NFR5: LLM scoring processes new jobs at 10 per minute without blocking API responses
- NFR6: JSearch API scrape run completes within 30 seconds for a single user's keyword set
- NFR7: Crawl4AI enrichment processes at minimum 20 pages per minute (with 3s pacing)

### Security

- NFR8: All API endpoints require Clerk authentication — unauthenticated requests return 401
- NFR9: User data isolation enforced via middleware — no cross-user data access possible
- NFR10: Resume PDF content (PII) transmitted to Google AI Studio over HTTPS only
- NFR11: API keys (Google AI Studio, JSearch, Clerk) stored as environment variables, never in code or client-side
- NFR12: Database credentials not exposed in application logs or error responses
- NFR13: CORS restricted to Vercel frontend origin only

### Integration

- NFR14: JSearch API — graceful handling of 429 rate limits, 5xx errors, and timeouts with retry
- NFR15: Google AI Studio — graceful handling of rate limits (15 RPM free tier), quota exhaustion, and model unavailability
- NFR16: Crawl4AI — exponential backoff on 429/503, circuit breaker disables portal after repeated failures
- NFR17: Clerk — session token validation on every request, graceful handling of Clerk API outages (deny access, don't crash)
- NFR18: All external API failures logged to `scrape_runs` or `usage_logs` with error details for debugging

### Reliability

- NFR19: Partial scraper failure (1-2 portals down) does not prevent remaining portals from completing
- NFR20: LLM service unavailability does not crash the API — scoring queues pause, document generation returns clear error
- NFR21: Database connection failures handled with retry (connection pool with auto-reconnect)
- NFR22: Cron scheduler survives API server restarts — jobs re-register on startup
- NFR23: No data loss on scrape failure — `last_successful_scrape_at` ensures gap recovery on next run

## Contract Updates Required

The following shared contracts need updating before implementation begins to reflect PRD decisions:

- **`contracts/db-schema.sql`**: Add `user_id UUID NOT NULL` to all tables, change unique constraint on jobs to `(user_id, portal, external_id)`, change settings PK to `(user_id, key)`, change `scraped_via_enum` from `jobspy` to `jsearch`
- **`contracts/openapi.yaml`**: Add `Authorization: Bearer` header to all endpoints, add 401 responses, update `scraped_via` enum to `jsearch`
- **`contracts/llm-schemas.json`**: Add `suggested_roles: string[]` to ParsedResume output schema
