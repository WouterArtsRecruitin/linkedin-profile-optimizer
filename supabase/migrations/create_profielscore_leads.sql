-- ============================================
-- Profielanalyse.nl — Lead Capture Table
-- Project: vrzwupnqwodqdtnmtwse
-- Plak dit in Supabase SQL Editor en klik RUN
-- ============================================

CREATE TABLE IF NOT EXISTS profielscore_leads (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  linkedin_url text NOT NULL,
  email text UNIQUE NOT NULL,
  status text DEFAULT 'nieuw',
  source text DEFAULT 'profielscore-landing',
  created_at timestamptz DEFAULT now()
);

-- Index voor snelle email lookups
CREATE INDEX IF NOT EXISTS idx_profielscore_leads_email 
  ON profielscore_leads(email);

-- Index voor status filtering (dashboard queries)
CREATE INDEX IF NOT EXISTS idx_profielscore_leads_status 
  ON profielscore_leads(status);

-- Row Level Security aan (service key bypast dit automatisch)
ALTER TABLE profielscore_leads ENABLE ROW LEVEL SECURITY;

-- Verifieer aanmaak
SELECT 'Tabel profielscore_leads aangemaakt ✅' AS resultaat;
