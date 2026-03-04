-- =============================================
-- LinkedIn Profile Optimizer — Supabase Schema
-- =============================================
-- Voer dit uit in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/jdistoacicmzdazdaubh/sql

-- Tabel: leads (Form 1 submissions)
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Form 1 data
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    linkedin_url TEXT NOT NULL,
    linkedin_goal TEXT,
    wants_banner BOOLEAN DEFAULT TRUE,
    privacy_consent BOOLEAN DEFAULT TRUE,
    
    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'scraping', 'needs_form2', 'analyzing', 'completed', 'failed')),
    
    -- LinkedIn scraped data (via Clay of eigen scraper)
    scraped_headline TEXT,
    scraped_about TEXT,
    scraped_job_title TEXT,
    scraped_employer TEXT,
    scraped_location TEXT,
    scraped_experience JSONB,
    scraped_skills JSONB,
    scraped_education JSONB,
    scraped_profile_photo_url TEXT,
    scraped_raw JSONB,
    
    -- Form 2 data (aanvullend, optioneel)
    form2_submitted BOOLEAN DEFAULT FALSE,
    form2_headline TEXT,
    form2_about TEXT,
    form2_job_title TEXT,
    form2_employer TEXT,
    form2_years_experience TEXT,
    form2_job_description TEXT,
    form2_top_skills TEXT,
    form2_unique_value TEXT,
    form2_target_sector TEXT,
    form2_target_audience TEXT,
    form2_profile_photo_url TEXT,
    form2_banner_style TEXT,
    form2_banner_color TEXT,
    
    -- Analyse resultaat
    analysis_score INTEGER,
    analysis_grade TEXT,
    analysis_result JSONB,
    report_html TEXT,
    mockup_html TEXT,
    banner_url TEXT,
    
    -- Delivery
    report_sent_at TIMESTAMPTZ,
    report_email_id TEXT,
    
    -- JotForm refs
    jotform_submission_id TEXT,
    jotform_form2_submission_id TEXT
);

-- Index op email (voor opzoeken)
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- Index op status (voor queue processing)
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

-- Index op created_at (voor cleanup na 30 dagen)
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

-- RLS Policies (Row Level Security)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Service role kan alles (voor de backend)
CREATE POLICY "Service role full access" ON leads
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Cleanup functie: verwijder leads ouder dan 30 dagen (AVG compliance)
CREATE OR REPLACE FUNCTION cleanup_old_leads()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM leads WHERE created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
