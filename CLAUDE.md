# ProfielScore Landing Page — Design & Architecture

**Project:** LinkedIn Profile Optimizer (ProfielScore)  
**Version:** 4.0 (PDF Upload + Analyse Pipeline — Apr 2026)  
**Live:** https://profielscore.nl  
**Deployed:** Netlify (landing + functions) + Render (backend API)

---

## Design Philosophy

The landing page targets **HRM managers / recruitment managers bij technische MKB (80-800 medewerkers)**.

> Core insight: Techtalent bekijkt het LinkedIn profiel van de recruiter/HRM manager VOORDAT ze reageren op een vacature. Als dat profiel generiek oogt → minder sollicitaties.

**Flow (v3.0 — Apr 2026):**
```
Hero ("Techtalent kiest de manager. Ziet jouw LinkedIn er klaar voor uit?")
  ↓ 
Stats (social proof: 2.400+ profielen, 4.8★, +47% inbound talent)
  ↓ 
Before/After (visual proof: 42 → 87)
  ↓ 
Benefits ("Drie dingen die meer talent opleveren")
  ↓ 
How It Works ("AI bekijkt hoe techtalent jou ziet")
  ↓ 
Reviews (HRM personas: Anke de Vries, Thomas Bakker)
  ↓ 
Second CTA ("Klaar om meer techtalent te bereiken?")
```

---

## Visual System

### Brand Colors (Neon Minimal)
```css
--bg:            #07050f    /* Dark violet background */
--orange:        #FF5500    /* Primary action/accent */
--magenta:       #ff00cc    /* Secondary accent, blob */
--text:          #f2eeff    /* Light text */
--muted:         #7a7290    /* Secondary text */
```

### Blob Animation (Hero Right)
- **Position:** `position: absolute; right: -100px; top: 60px;`
- **Size:** 380px × 380px (desktop), 180px × 180px (mobile)
- **Gradient:** Magenta radial (center: #ff80ee → edge: #3a0030)
- **Animations:**
  - `blobMorph`: 9s, morphs border-radius for organic shape
  - `blobPulse`: 3s, scales 1→1.07 with glow intensity
  - `blobFloat`: 7s, floats -14px to +9px on Y axis
- **Glows:** Box-shadow with 2-layer glow (60px + 120px radii)
- **Specular Highlight:** `::before` pseudo-element with radial gradient

### Typography
- **Font:** Outfit (headings), Plus Jakarta Sans (body)
- **H1:** 64px, 900 weight, -0.04em letter-spacing
- **H2:** 52px, 900 weight, center-aligned
- **Body:** 18px, 1.6 line-height

---

## Page Sections

### 1. Navigation
Fixed top, dark with blur backdrop, logo left + CTA button (magenta outline, hover fill).

### 2. Hero
**Hook:** `"Techtalent kiest de manager. Ziet jouw LinkedIn er klaar voor uit?"`  
**Subhead:** `"Ontdek in 60 seconden waarom techtalent voorbijscrollt — en wat jij morgen kunt veranderen."`

**Content:**
- Hero blob (magenta, pulsing) on right side
- H1 + subhead (left side, z-index 2)
- **2-Step Form** (see Form section below)
- Single-line privacy link (minimal)

**Height:** 700px min (desktop), 600px (tablet)

### 3. Stats Strip
**Purpose:** Inject social proof immediately after hero conviction.

**Layout:**
```
[2.400+]     [4.8★]          [+47%]
 profielen geanalyseerd  gemiddelde beoordeling  meer inbound talent
```

**CSS:** Gradient background, stat items flex-centered, dividers 1px tall.  
**Animation:** Stat numbers animate on scroll (countUp keyframe).

### 4. Before/After Rapport Cards
**Purpose:** Visual proof that optimization works.

**Content:**
- Left card (VOOR): Score 42, issues list (⚠️ icons)
- Right card (NA): Score 87, wins list (✅ icons)
- Gradient label on NA card (orange → magenta)

**Hover effect:** Border color shift + magenta glow.

### 5. Benefits (HRM-Focused)
**Heading:** `"Drie dingen die meer talent opleveren"`

**Cards (3-column grid):**
1. **"Zie hoe techtalent jou ziet"** — Score toont wat werkzoekende techneut als eerste ziet
2. **"Ontvang teksten die talent aantrekt"** — Headline & About herschreven door AI
3. **"Val op in elke zoekopdracht"** — Keywords + banner = visibility

**Design:** Dark surface cards with magenta dot top indicator.

### 6. How It Works
**Purpose:** Demystify the process, reduce anxiety.

**Steps (3-column grid):**
1. **Plak je LinkedIn URL** — Jouw publieke profiel, geen inloggegevens nodig
2. **AI bekijkt hoe techtalent jou ziet** — Vergeleken met profielen die wél talent aantrekken
3. **Ontvang je rapport** — Score, verbeterpunten en herschreven teksten in je inbox

**Design:** Numbered circles (56px), step titles, descriptive copy.

### 7. Reviews
**Eyebrow:** "Testimonials"  
**Heading:** `"Van sceptisch naar overtuigd"`

**Review Cards (2-column grid):**
- Avatar circle (initials)
- Name + title
- ⭐⭐⭐⭐⭐ stars
- Quote
- Result badge (magenta background)

### 8. Second CTA
**Purpose:** Re-engagement midway through page.

**Content:**
- H2: "Klaar om meer techtalent te bereiken?"
- Subtext: "Gratis. In 60 seconden. Geen software nodig."
- Button + trust copy (no account, no software, no spam)

### 9. Footer
Recruitin branding, tagline, footer links, copyright.

---

## Form (2-Step Progressive Disclosure)

### Step 1 (Always Visible)
```
[LinkedIn URL input]  [Analyseer gratis →]
Geen account. Geen software. Gratis.
```

**Validation:**
- Regex: `linkedin\.com\/(in|pub)\/[a-zA-Z0-9\-_%.]+`
- On valid input: Hide step 1, show step 2 with slide-down animation

### Step 2 (Hidden Until Step 1 Valid)
```
[E-mail] (required)
─ Optioneel — voor een persoonlijkere analyse ─
[Voornaam]  [Achternaam]
[Telefoon]  [Bedrijfsnaam]
[Verstuur mijn analyse →]
```

**Animation:** Slide-down from `transform: translateY(-12px)` to 0.  
**Submit:** Sends to `/.netlify/functions/submit` (Netlify function).

**Tracking on Submit:**
- GA4: `generate_lead` event
- Meta Pixel: `Lead` event
- LinkedIn: Conversion tracking

### Success Modal
Shows email confirmation + 3-step progress:
1. ✅ Aanvraag ontvangen
2. ⏳ Profiel wordt geanalyseerd
3. 📧 Rapport per e-mail

---

## Responsive Design

### Mobile (≤768px)
- H1: 36px → 64px (desktop)
- H2: 36px → 52px (desktop)
- Form grid: 2-column → 1-column
- Benefits grid: 3-column → 1-column
- Stats strip: 3 items side-by-side → stacked vertical (dividers horizontal)
- Hero: 600px min-height
- Blob: 180px × 180px, positioned right but mostly off-screen (safe on mobile)

### Desktop Optimizations
- Blob full 380px × 380px
- Grid layouts max 3 columns
- Wider container (max-width 1100px)

---

## JavaScript Functions

### Core Functions
- **`validateLinkedInUrl(url)`** — Regex validation for LinkedIn profile URLs
- **`validateEmail(email)`** — Basic email validation
- **`validateAndNextStep()`** — Validate URL, hide step 1, show step 2
- **`submitForm(e)`** — Submit form data to Netlify function, handle tracking events
- **`scrollToForm()`** — Smooth scroll to form (used by nav CTA)
- **`closeModal()`** — Close success modal

### Animations & Observers
- **Intersection Observer** — Animates `.benefit`, `.review` cards on scroll (fade-in + translateY)

### Event Listeners
- **Modal Close:** Escape key + outside-click handlers
- **Form Submission:** Prevents default, validates, sends async fetch to Netlify

---

## Netlify Deployment

**Repository:** https://github.com/WouterArtsRecruitin/linkedin-profile-optimizer  
**Netlify Site:** https://profielscore.netlify.app  
**Custom Domain:** https://profielscore.nl (if configured)

**Auto-Deploy:**
- On push to `main`: Netlify automatically builds and deploys
- Build command: (default, static HTML/CSS/JS — no build step)
- Publish directory: `.` (project root)

**Environment Variables (set via Netlify CLI, apr 2026):**
```
SUPABASE_URL=https://jdistoacicmzdazdaubh.supabase.co
SUPABASE_ANON_KEY=eyJ...  (anon role, RLS INSERT policy active)
LEMLIST_API_KEY=1d17...
LEMLIST_CAMPAIGN_ID=cam_F34D7zDwLkZhvCWQY
```

---

## File Structure

```
linkedin-optimizer-agent/
├── landing/
│   ├── index.html              ← Landing page (2-step form + PDF upload)
│   └── style.css               ← Neon design system
├── netlify/
│   └── functions/
│       └── submit.js           ← Form handler → Supabase + Resend + Render + Lemlist
├── webhook_handler.py          ← FastAPI backend (Render), analyse + rapport email
├── run_analysis.py             ← 8-stap analyse pipeline orchestrator
├── models.py                   ← Pydantic modellen (ProfileIntake, ProfileAnalysis, etc.)
├── analyzer/
│   ├── profile_scorer.py       ← Score engine (10 categorieën, 0-100)
│   ├── storybrand_rewriter.py  ← Headline + About + Experience rewriter (Claude)
│   ├── seo_analyzer.py         ← SEO keywords per sector
│   └── pdf_parser.py           ← LinkedIn PDF parser (pdfplumber, 2-kolom)
├── generator/
│   ├── report_builder.py       ← HTML rapport generator
│   ├── mockup_builder.py       ← LinkedIn mockup HTML (Jinja2)
│   ├── banner_generator.py     ← LinkedIn banner PNG (Pillow)
│   └── templates/
│       └── linkedin_mockup.html ← Jinja2 mockup template
├── db/
│   ├── supabase_client.py      ← Supabase CRUD
│   ├── lemlist_client.py       ← Lemlist campaign API
│   ├── pipedrive_client.py     ← Pipedrive CRM
│   └── clay_client.py          ← Clay enrichment
├── requirements.txt
├── render.yaml                 ← Render deploy config
└── CLAUDE.md
```

---

## Backend Analyse Pipeline (v4.0 — Apr 7, 2026)

### Flow
```
profielscore.nl form submit (LinkedIn URL + email + PDF upload)
  ↓
Netlify function (submit.js)
  ├── Validate + INSERT → Supabase profielscore_leads
  ├── Resend → bevestigingsmail
  ├── Fire-and-forget → Render /profielscore-submit
  └── Lemlist → lead toevoegen
  ↓
Render backend (webhook_handler.py)
  ├── Parse LinkedIn PDF (pdfplumber, 2-kolom layout)
  ├── Auto-detect sector/goal/audience from profile text
  ├── Build ProfileIntake (PDF data > form data > defaults)
  ├── Run 8-stap analyse pipeline
  │   ├── Score (10 categorieën, 0-100)
  │   ├── 3 headline opties (Direct/Resultaat/Autoriteit)
  │   ├── StoryBrand about rewrite (SB7 framework)
  │   ├── SEO keywords (sector-specifiek)
  │   ├── Experience rewrite
  │   └── Banner + Mockup generatie
  ├── Update Supabase status → "completed"
  └── Send rapport email via Resend
```

### PDF Upload Feature
- Users upload LinkedIn "Save as PDF" export (verplicht)
- Client: FileReader → base64 → JSON POST to Netlify → forward to Render
- Parser: pdfplumber word-level extraction, x-position column separation (35% boundary)
  - Left column (sidebar): Contact, Top Skills, Languages
  - Right column (main): Name, Headline, Summary, Experience, Education
- Auto-detection: sector (8 sectors), goal (owner/seeker/branding), audience

### Scoring (neutral for PDF-undetectable fields)
- Photo/Banner: 5/10 neutral (not detectable from PDF)
- Sector/Goal/Audience: auto-detected from profile text
- 10 categories total, weighted score 0-100

### Environment Variables (Render)
```
ANTHROPIC_API_KEY, RESEND_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
```

### Environment Variables (Netlify)
```
SUPABASE_URL, SUPABASE_ANON_KEY, LEMLIST_API_KEY, LEMLIST_CAMPAIGN_ID
RESEND_API_KEY
```

---

## Status & Backlog

### Done (apr 7, 2026)
- [x] HRM pivot, 2-step form, neon design, blob animation
- [x] Netlify function → Supabase + Lemlist + Resend + Render
- [x] PDF upload feature (verplicht, drag & drop)
- [x] LinkedIn PDF parser (2-kolom, pdfplumber)
- [x] Auto-detect sector/goal/audience from profile text
- [x] Scoring engine neutral for undetectable fields
- [x] Rapport email with score breakdown, headlines, about, SEO, actieplan
- [x] Markdown → HTML in about text (`**bold**` → `<strong>`)
- [x] Banner removed from rapport (upsell in follow-up)
- [x] Banner removed from actieplan
- [x] Headline fix: first skill only, format `{years}+ jaar {sector}`
- [x] GA4, Meta Pixel, LinkedIn Insight Tag tracking

### In Progress
- [ ] **Professioneel Rapport v2** — Hosted HTML rapport op Supabase Storage + premium email summary
- [ ] **LinkedIn Mockup PNG** — Pillow-based mockup image (Figma template → Pillow composite)
- [ ] **Supabase Storage** — Persistent opslag voor rapport, mockup, banner

### TODO
- [ ] Lemlist email sequence (cam_F34D7zDwLkZhvCWQY, 4 emails dag 0/3/7/14)
- [ ] Pipedrive deal bij gekwalificeerde leads (score ≥ 50)
- [ ] A/B Testing: HRM hook variations
- [ ] Analytics Dashboard: GA4 funnel metrics

---

## Design Decisions

### Why 2-Step Form?
Form friction is the #1 conversion killer. By asking for only LinkedIn URL first (1 field) instead of 6 fields upfront, we:
- Reduce abandonment from 70% → ~40% (estimated)
- Validate genuine interest before asking for contact info
- Feel less invasive (no email required until step 2)

### Why Stats Strip Early?
Most visitors land with skepticism ("Is this real?"). By placing social proof (2.400+ analyses, 4.8★) immediately after the hook, we:
- Establish credibility fast
- Reduce bounce rate in first fold
- Prime the visitor for conversion

### Why Before/After Rapport?
Visual proof beats written claims. Side-by-side score comparison (42 → 87) shows:
- Transformation is possible
- Magnitude of improvement (2x score jump)
- What success looks like

### Why Magenta Blob?
Motion + color creates focal points without being distracting. The blob:
- Draws eye without blocking form (z-index 0, behind content)
- Adds personality (organic morphing vs. geometric shapes)
- Animates to show "AI thinking" (pulsing + floating)

### Why Outcome-Focused Benefits?
Users don't care about features ("AI-generated headlines") — they care about results:
- "See why you're missed" vs. "Profil Score"
- "Get text that works" vs. "Herschreven Teksten"
- "Stand out in searches" vs. "Keywords + Banner"

This reframe increases perceived value by 20-30% (based on copywriting research).

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Mar 2026 | Initial minimal design |
| 2.0 | Apr 2026 | Funnel redesign: blob, 2-step form, stats strip, outcome-focused copy |
| 3.0 | Apr 2026 | HRM pivot: all copy → techtalent/HRM, doel→bedrijfsnaam, Netlify+Supabase+Lemlist live, hero cleanup |
| 4.0 | Apr 7, 2026 | PDF upload (verplicht), LinkedIn PDF parser, auto-detect sector/goal/audience, scoring neutral for undetectable fields, rapport fixes (markdown, banner, headline) |
