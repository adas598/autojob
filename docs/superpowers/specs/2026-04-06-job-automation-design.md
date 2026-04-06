# Job Automation Tool — Design Spec
**Date:** 2026-04-06  
**Status:** Approved

---

## Overview

A locally-run job automation tool that handles the tedious parts of job searching — finding relevant listings, preparing tailored applications and cover letters — while keeping the user in full control via a daily review dashboard. Built for personal use first (Australian job market), with a clear path to productization later.

---

## Goals

- Eliminate the stress and repetition of manually searching and applying for jobs
- Monitor Australian job sources daily and surface only relevant matches
- Prepare complete, tailored applications ready for user review
- User approves and manually submits — tool never auto-submits
- All data stays local (no cloud, no third-party storage)

---

## Non-Goals (for now)

- Windows background service / startup automation (future enhancement)
- Multi-user support (personal use only for now)
- Automated form submission (by design — user always hits submit)
- International job boards

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User's Machine                      │
│                                                      │
│  ┌─────────────┐    ┌──────────────────────────┐    │
│  │  Scheduler  │───▶│     Job Scraper          │    │
│  │ (on app     │    │ SEEK / Gov Portals /     │    │
│  │  start)     │    │ Company Career Pages     │    │
│  └─────────────┘    └──────────┬───────────────┘    │
│                                │                     │
│                     ┌──────────▼───────────────┐    │
│                     │   Matching Engine         │    │
│                     │ (Claude API)              │    │
│                     └──────────┬───────────────┘    │
│                                │                     │
│                     ┌──────────▼───────────────┐    │
│                     │  Application Preparer     │    │
│                     │ (Claude API)              │    │
│                     └──────────┬───────────────┘    │
│                                │                     │
│                     ┌──────────▼───────────────┐    │
│                     │   SQLite Database         │    │
│                     └──────────┬───────────────┘    │
│                                │                     │
│                     ┌──────────▼───────────────┐    │
│                     │   Web Dashboard           │    │
│                     │   localhost:3000          │    │
│                     └──────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Tech stack:**
- Backend: Python + FastAPI
- Frontend: React
- Database: SQLite
- AI: Claude API (claude-sonnet-4-6)
- Scraping: Playwright (browser automation, rate-limited)

---

## Components

### 1. Scheduler
- Triggers on app start, but only if scraping hasn't already run today (checked via last-run timestamp in DB)
- Runs scraping + matching pipeline in the background — dashboard is usable immediately while it runs
- User starts the app manually — no Windows service (future enhancement)

### 2. Job Scraper
- Sources:
  - SEEK (Australian job board)
  - NSW Government Jobs (I Work for NSW portal)
  - Federal Government (APSJobs)
  - User-defined company career page watchlist
- Extracts: job title, description, requirements, location, salary, application URL, date posted
- Respects `robots.txt`, rate-limits requests
- Deduplicates via SQLite — same job URL never processed twice

### 3. Matching Engine
- Claude API compares each job description against the user's profile
- Scores jobs: **Strong Match / Possible Match / Weak Match**
- Filters applied automatically:
  - Jobs requiring PR or citizenship (based on visa profile)
  - User-defined exclusion keywords/companies
- Only Strong and Possible matches proceed to Application Preparer
- Weak matches are stored in DB but not surfaced in dashboard

### 4. Application Preparer
- Runs Claude API for each matched job to produce:
  - **Cover letter** — tailored to the job, written in the user's voice (inferred from resume + optional writing sample)
  - **Application answers** — pre-filled responses to standard fields and selection criteria (common in government applications)
  - **Visa/work rights** — automatically populated from profile (485 visa, full work rights)
- Stores a reusable answer template for common fields to avoid redundant generation
- All outputs are editable by the user before submission

### 5. SQLite Database
Schema covers:
- `profile` — user details, skills, visa info, preferences
- `jobs` — all scraped jobs with status (pending / approved / rejected / applied)
- `applications` — prepared cover letters and form answers per job
- `sources` — company watchlist and job board toggles
- `applied_history` — tracking post-approval status (Applied, Interview, Offer, Rejected)

### 6. Web Dashboard (`localhost:3000`)

**Job Queue view:**
- Cards sorted by match score (Strong first)
- Each card: job title, company, location, match score, date found

**Job Review view:**
- Left: full job description
- Right: editable cover letter + application answers
- "Open Application Page" button — opens real job site in browser
- Approve / Reject actions

**Applied view:**
- History of approved applications
- Manual status updates (Applied → Interview → Offer / Rejected)

**Settings view:**
- Profile editor (name, contact, skills, experience, education, visa status, salary expectations, location preferences, exclusions)
- Resume upload (PDF/Word — auto-extracts to profile)
- Writing sample upload (optional — used to match cover letter voice)
- Company watchlist manager
- Job source toggles (SEEK, Gov portals)

---

## User Profile

Stored locally in SQLite. Contains:

| Field | Source |
|-------|--------|
| Name, contact details | Resume / manual |
| Work history | Resume (auto-extracted) |
| Skills | Resume (auto-extracted) + manual fine-tune |
| Education & certifications | Resume (auto-extracted) |
| Target job title(s) | Manual — primary + acceptable nearby roles |
| Preferred location | Manual |
| Salary expectations | Manual (optional) |
| Visa type | Manual — 485 (Temporary Graduate) |
| Visa expiry | Manual |
| Work rights | Auto-set: Full work rights |
| Exclusions | Manual — industries, companies, keywords to skip |
| Job sources | Manual — which boards/companies to monitor |

---

## Ethical & Legal Considerations

- Tool never auto-submits applications — user always manually submits on the job site
- Scraping is rate-limited and respects `robots.txt`
- No circumvention of CAPTCHAs or anti-bot measures
- Official APIs used where available; scraping used only as fallback
- All user data stored locally — never sent to third parties except Claude API for AI processing

---

## Future Enhancements

- Windows background service (auto-start on boot, scrape without opening app)
- Email/desktop notifications when new jobs are queued
- Multi-user / hosted web app version (productization path)
- LinkedIn integration for job discovery (not application submission)
- Interview preparation assistant
- Application analytics (response rates by job type, company, etc.)

---

## Success Criteria

- Tool surfaces 5–10 relevant, pre-filtered job matches per day
- Each application takes user less than 5 minutes to review and approve
- Zero accidental submissions — user is always the final action
- Runs reliably on a Windows 11 machine with a single start command
