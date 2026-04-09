# AutoJob

Job application automation tool that scrapes job boards, scores opportunities against your resume using an LLM, and generates tailored resumes and cover letters from templates — turning a found job into a ready-to-submit application in under 60 seconds. Built for two users (Ayush and Aneet) with independent scraping configs, scoring, and application tracking.

## Quick Links

| Document | Description |
|----------|-------------|
| [PRD](_bmad-output/planning-artifacts/prd.md) | Product Requirements Document — 57 FRs, 23 NFRs, user journeys, scoping |
| [Design Spec](docs/superpowers/specs/2026-04-06-autojob-design.md) | Technical design specification (v2) |
| [DB Schema](contracts/db-schema.sql) | PostgreSQL schema — 7 tables, enums, indexes |
| [API Spec](contracts/openapi.yaml) | OpenAPI 3.1 — 19 endpoints |
| [LLM Schemas](contracts/llm-schemas.json) | LLM input/output JSON schemas for scoring + template filling |

> **Note:** The contracts need updating to reflect PRD decisions (user_id scoping, JSearch replacing JobSpy, Clerk auth). See "Contract Updates Required" section at the bottom of the PRD.

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14+ (App Router) + Tailwind CSS on Vercel |
| Backend | FastAPI (async) on Railway ($20/mo plan) |
| Database | PostgreSQL on Railway |
| Auth | Clerk OAuth (2 users, independent accounts) |
| Job Discovery | JSearch API (pay-as-you-go $0.005/req) |
| Job Enrichment | Crawl4AI (full JD, visa info) + Seek.com.au scraping |
| LLM | Gemma 4 31B via Google AI Studio (free tier), abstracted via LangChain |
| Document Gen | docxtpl (Jinja2 in DOCX) + PDF conversion |
| Scheduling | APScheduler (per-user cron jobs) |

## Development Tracks

Two parallel tracks — each developer works independently, integrating at defined points.

### Track A: Data Pipeline (Ayush)

| Task | Description | Effort |
|------|-------------|--------|
| A1 | Project scaffold, DB models, CRUD APIs | 0.5 day |
| A2 | JSearch API integration (LinkedIn, Indeed, Glassdoor, Google Jobs) | 1 day |
| A3 | Crawl4AI Seek.com.au scraper + enrichment | 1.5 days |
| A4 | APScheduler cron jobs (per-user) | 0.5 day |
| A5 | Job scoring/ranking (uses LLM layer from Track B) | 1 day |
| A6 | Docker + Railway deploy | 0.5 day |

### Track B: Documents & UI (Aneet)

| Task | Description | Effort |
|------|-------------|--------|
| **B1** | **LangChain LLM abstraction layer — FIRST DELIVERABLE (Day 2)** | **0.5 day** |
| B2 | Resume parser (PyMuPDF + LLM structuring) | 0.5 day |
| B3 | docxtpl template system (resume + cover letter, DOCX + PDF) | 1.5 days |
| B4 | Application tracking API | 0.5 day |
| B5 | Next.js frontend dashboard | 2-3 days |

### Critical Integration Points

1. **B1 (LLM layer) must ship before A5 (scorer)** — Ayush creates an LLM stub on Day 1 to unblock
2. **A1 (DB schema) must ship before B2/B3/B4** — Aneet builds against the models
3. **API spec agreed upfront** — both tracks build to `contracts/openapi.yaml`

## For Aneet: Getting Started with BMAD

This project uses [BMAD](https://github.com/bmad-method/bmad) for structured product development. The BMAD agent skills and workflows are checked into the repo at `_bmad/` and `.claude/skills/`.

### Understanding What Happened

The PRD was created through a comprehensive 12-step BMAD workflow with multiple rounds of multi-agent review (party mode). To understand the decisions:

1. **Read the PRD first:** `_bmad-output/planning-artifacts/prd.md` — this is the source of truth for all product decisions
2. **Read the design spec:** `docs/superpowers/specs/2026-04-06-autojob-design.md` — technical details
3. **Read the contracts:** `contracts/` — the shared interfaces you'll build against

### Key BMAD Skills You'll Use

Run these in Claude Code (CLI or IDE) from the project root:

| Command | What It Does | When To Use |
|---------|-------------|-------------|
| `/bmad-help` | Analyzes project state and recommends next skill | When unsure what to do next |
| `/bmad-validate-prd` | Validates the PRD against standards | Before starting architecture |
| `/bmad-create-architecture` | Creates technical architecture doc | After PRD is validated |
| `/bmad-create-epics-and-stories` | Breaks PRD into epics and user stories | After architecture is done |
| `/bmad-create-story` | Creates a detailed story file for implementation | When ready to code a story |
| `/bmad-dev-story` | Implements a story following its spec | To code against a story |
| `/bmad-party-mode` | Multi-agent discussion on any topic | When you want diverse perspectives |
| `/bmad-agent-pm` | Talk to John (PM) about requirements | Clarify PRD decisions |
| `/bmad-agent-architect` | Talk to Winston about architecture | Technical design questions |

### Recommended Workflow for Aneet

```
1. Read PRD → understand the full product vision and your Track B tasks
2. /bmad-validate-prd → ensure PRD is implementation-ready
3. /bmad-create-architecture → create the technical architecture doc
4. /bmad-create-epics-and-stories → break Track B into implementable stories
5. /bmad-create-story → create your first story (B1: LLM abstraction layer)
6. /bmad-dev-story → implement B1
7. Repeat 5-6 for B2, B3, B4, B5
```

### Installing BMAD Skills

The skills are already in the repo. If Claude Code doesn't pick them up automatically:

```bash
# The _bmad/ directory contains all agent definitions and workflows
# The .claude/skills/ directory contains the skill entry points
# Both are checked into git — no installation needed
```

## Local Setup

```bash
# Clone
git clone https://github.com/adas598/autojob.git
cd autojob

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys (Google AI Studio, JSearch, Clerk)

# Database (requires PostgreSQL running locally)
createdb autojob
createdb autojob_test
alembic upgrade head

# Run
uvicorn app.main:app --reload
```

## Project Structure

```
auto-job/
├── backend/                     # FastAPI (Railway)
│   ├── app/
│   │   ├── api/                 # Route handlers
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── scrapers/            # JSearch + Crawl4AI
│   │   ├── services/            # LLM, scorer, resume gen, cover letter
│   │   └── templates/           # DOCX templates
│   ├── alembic/                 # DB migrations
│   └── tests/
├── frontend/                    # Next.js (Vercel) — Track B, later
├── contracts/                   # Shared schemas & API spec
│   ├── db-schema.sql
│   ├── openapi.yaml
│   └── llm-schemas.json
├── _bmad/                       # BMAD agent library
├── _bmad-output/                # Generated artifacts (PRD, etc.)
├── .claude/skills/              # BMAD skill entry points
└── docs/superpowers/specs/      # Design specifications
```

## Cost Model

| Component | Monthly |
|-----------|---------|
| Railway ($20 plan) | $20 |
| JSearch API (2 users) | $4-6 |
| Google AI Studio (Gemma 4 31B) | $0 (free tier) |
| Vercel (frontend) | $0 (free tier) |
| Clerk (auth) | $0 (free tier, 2 users) |
| **Total** | **~$24-26/month** |
