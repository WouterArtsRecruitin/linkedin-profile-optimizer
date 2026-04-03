# Profielscore Landing Page — Setup Checklist

## 1. Supabase: Add form fields to `profielscore_leads` table

Run this migration in Supabase SQL Editor:

```sql
-- Alter table to add missing columns
ALTER TABLE profielscore_leads
ADD COLUMN IF NOT EXISTS voornaam VARCHAR(255),
ADD COLUMN IF NOT EXISTS achternaam VARCHAR(255),
ADD COLUMN IF NOT EXISTS telefoonnummer VARCHAR(20),
ADD COLUMN IF NOT EXISTS doel VARCHAR(100),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profielscore_leads_updated_at ON profielscore_leads;

CREATE TRIGGER update_profielscore_leads_updated_at
BEFORE UPDATE ON profielscore_leads
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
```

**Status:** ⏳ TODO

---

## 2. Lemlist: Create new campaign `cam_profielscore`

**Campagne naam:** Profielscore — Profile Optimization Lead Funnel
**Campaign ID:** `cam_profielscore` (will be auto-assigned, update below)

**Fields to configure:**
- **Email:** (auto-mapped from form)
- **firstName:** Voornaam (optional)
- **lastName:** Achternaam (optional)
- **Phone:** Telefoonnummer (optional)
- **customField (doel):** meer-profielweergaven | recruiter-contact | alles-optimaliseren

**Email sequence:** (to be created)
- Day 0: Welcome + PDF attachment
- Day 3: Tips based on their doel
- Day 7: Social proof + case studies

**Status:** ⏳ TODO

---

## 3. Netlify: Set environment variables

In Netlify > Deploy settings > Environment:

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
LEMLIST_API_KEY=your_lemlist_api_key
```

**Status:** ⏳ TODO

---

## 4. Test form

1. Open https://profieloptimizer.netlify.app
2. Fill form:
   - LinkedIn URL: https://linkedin.com/in/wouter-arts
   - Email: test@example.com
   - Voornaam: Wouter
   - Achternaam: Arts
   - Telefoonnummer: +31614314593
   - Doel: meer-profielweergaven
3. Click "Ontvang mijn rapport →"
4. Verify:
   - Supabase: New row in `profielscore_leads` with all fields ✅
   - Lemlist: Lead added to campaign ✅
   - Modal: "Je rapport is onderweg!" appears ✅

**Status:** ⏳ TODO

---

## 5. (Optional) JotForm migration

If you want to keep JotForm integration:
- Create new form at jotform.com
- Map fields: linkedin_url (Q1), email (Q2), voornaam (Q3), achternaam (Q4), telefoonnummer (Q5), doel (Q6)
- Update `submit.js` Jotform endpoint URL
- Add back Jotform API call (currently removed)

**Status:** ⏳ SKIPPED (using Supabase + Lemlist direct)

---

## Deployment

✅ **Code deployed:** https://github.com/WouterArtsRecruitin/linkedin-profile-optimizer (commit: 68e241d)

⏳ **Awaiting:**
1. Supabase migration
2. Lemlist campaign creation
3. Netlify env vars
4. Test form submission
