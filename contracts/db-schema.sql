-- AutoJob v2 Database Schema
-- Shared contract: both Track A and Track B must implement against this schema.

-- Enums
CREATE TYPE job_type_enum AS ENUM ('full_time', 'part_time', 'contract', 'intern');
CREATE TYPE seniority_enum AS ENUM ('junior', 'mid', 'senior', 'lead', 'exec');
CREATE TYPE portal_enum AS ENUM ('linkedin', 'indeed', 'glassdoor', 'google_jobs', 'seek');
CREATE TYPE scraped_via_enum AS ENUM ('jobspy', 'crawl4ai');
CREATE TYPE scrape_status_enum AS ENUM ('running', 'success', 'failed');
CREATE TYPE application_status_enum AS ENUM ('generated', 'applied', 'interview', 'rejected', 'offer');
CREATE TYPE usage_operation_enum AS ENUM ('score', 'resume_gen', 'cover_letter_gen', 'parse');

-- Resumes
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name VARCHAR NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_skills JSONB NOT NULL DEFAULT '[]',
    parsed_experience JSONB NOT NULL DEFAULT '[]',
    parsed_education JSONB NOT NULL DEFAULT '[]',
    pdf_blob BYTEA NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    salary_min INTEGER,
    salary_max INTEGER,
    job_type job_type_enum,
    seniority seniority_enum,
    visa_info VARCHAR,
    description TEXT NOT NULL,
    source_url VARCHAR NOT NULL,
    portal portal_enum NOT NULL,
    external_id VARCHAR NOT NULL,
    scraped_via scraped_via_enum NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (portal, external_id)
);

-- Job Scores
CREATE TABLE job_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    rubric_breakdown JSONB NOT NULL,
    reasoning TEXT NOT NULL,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    tailored_resume_pdf BYTEA,
    tailored_resume_docx BYTEA,
    tailored_content JSONB NOT NULL,
    cover_letter_pdf BYTEA,
    cover_letter_docx BYTEA,
    cover_letter_content JSONB NOT NULL,
    template_used VARCHAR NOT NULL,
    status application_status_enum NOT NULL DEFAULT 'generated',
    applied_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Scrape Runs
CREATE TABLE scrape_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portal portal_enum NOT NULL,
    scraped_via scraped_via_enum NOT NULL,
    status scrape_status_enum NOT NULL DEFAULT 'running',
    jobs_found INTEGER NOT NULL DEFAULT 0,
    jobs_new INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

-- Usage Logs
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation usage_operation_enum NOT NULL,
    model VARCHAR NOT NULL DEFAULT 'gemma-4-31b',
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Settings (key-value store)
CREATE TABLE settings (
    key VARCHAR PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Default settings
INSERT INTO settings (key, value) VALUES
    ('scrape_frequency', '"daily"'),
    ('scrape_portals', '["linkedin", "indeed", "glassdoor", "google_jobs", "seek"]'),
    ('match_threshold', '50'),
    ('top_k', '50'),
    ('search_keywords', '[]'),
    ('preferred_locations', '[]'),
    ('usage_cap_type', '"monthly"'),
    ('usage_cap_value', '10.00');

-- Indexes
CREATE INDEX idx_jobs_portal ON jobs(portal);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_job_scores_job_id ON job_scores(job_id);
CREATE INDEX idx_job_scores_resume_id ON job_scores(resume_id);
CREATE INDEX idx_job_scores_overall ON job_scores(overall_score DESC);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_scrape_runs_portal ON scrape_runs(portal);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
