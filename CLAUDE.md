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
│       ├── submit.js           ← Form handler → Supabase + Resend + Render + Lemlist
│       └── rapport.js          ← Proxy: fetch rapport HTML uit Supabase Storage, serve als text/html
├── webhook_handler.py          ← FastAPI backend (Render), analyse + rapport email
├── run_analysis.py             ← 8-stap analyse pipeline orchestrator
├── models.py                   ← Pydantic modellen (ProfileIntake, ProfileAnalysis, etc.)
├── analyzer/
│   ├── profile_scorer.py       ← Score engine (10 categorieën, 0-100)
│   ├── storybrand_rewriter.py  ← Headline + About + Experience rewriter (Claude)
│   ├── seo_analyzer.py         ← SEO keywords per sector
│   └── pdf_parser.py           ← LinkedIn PDF parser (pdfplumber, 2-kolom)
├── generator/
│   ├── report_builder.py       ← Hosted rapport + email summary builder (Jinja2)
│   ├── mockup_builder.py       ← LinkedIn mockup HTML (Jinja2)
│   ├── mockup_image_builder.py ← LinkedIn mockup PNG (Pillow, 1200×800)
│   ├── banner_generator.py     ← LinkedIn banner PNG (Pillow)
│   ├── storage_uploader.py     ← Supabase Storage upload (rapport, mockup, banner)
│   └── templates/
│       ├── linkedin_mockup.html  ← Jinja2 mockup template
│       ├── hosted_rapport.html   ← Jinja2 hosted rapport (dark ProfielScore brand)
│       ├── email_rapport.html    ← Jinja2 email summary (table-based, CTA)
│       └── fonts/                ← Gebundelde Inter fonts (Regular, SemiBold, Bold)
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
  ├── Generate mockup PNG (Pillow, 1200×800)
  ├── Upload → Supabase Storage (rapport.html, mockup.png, banner.png)
  ├── Build email summary (Jinja2, CTA → Netlify proxy → hosted rapport)
  ├── Send email via Resend
  └── Update Supabase (status=completed, score, grade, rapport_url, mockup_url)
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

### Done (apr 7, 2026 — rapport v2)
- [x] Hosted rapport op Supabase Storage (dark ProfielScore brand, Jinja2)
- [x] Premium email summary met CTA → hosted rapport
- [x] LinkedIn mockup PNG (Pillow, 1200×800, Inter fonts)
- [x] Supabase Storage uploads (rapport, mockup, banner) met upsert
- [x] Netlify proxy function (rapport.js) — Supabase serveert HTML als text/plain
- [x] Supabase schema: rapport_url, mockup_url, banner_url, score, grade kolommen
- [x] Score + grade opgeslagen in Supabase bij completion

### Rapport Architectuur
```
Email (compact summary)                    Hosted rapport (volledig)
├── Score cirkel + grade                   ├── Score breakdown (alle categorieën)
├── Top 3 categorieën                      ├── 3 headline opties + AANBEVOLEN badge
├── Aanbevolen headline                    ├── Herschreven About (copy-to-clipboard)
├── Mockup preview                         ├── SEO keyword pills
├── CTA → "Bekijk rapport"                 ├── Experience voor/na vergelijking
└── Recruitin footer                       ├── Actieplan (genummerd)
                                           ├── LinkedIn mockup image
                                           └── Print-to-PDF via window.print()
```

**Rapport URL flow:** Email CTA → Netlify `/.netlify/functions/rapport?path=...` → fetch van Supabase Storage → serve als `text/html`

### Done (apr 7, 2026 — Figma designs)
- [x] Figma file geüpdatet met 8 pages (file: `5mWJIMDO3NQwfN2wls8LoS`)
  - **ProfielScore** (4 pages): Landing Page, Hosted Rapport, LinkedIn Mockup, Email Template
  - **Kandidatentekort** (2 pages): Vacature Analyse Rapport, Email Template
  - **Recruitment APK** (2 pages): Audit Rapport, Email Template
- [x] Elk product heeft unieke brand, content en secties (niet copy-paste)

### TODO
- [ ] Gegenereerde teksten fixen — storybrand_rewriter.py gebruikt GEEN AI, alles is f-string templates
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
| 4.0 | Apr 7, 2026 | PDF upload, LinkedIn PDF parser, auto-detect sector/goal/audience, scoring neutral for undetectable fields |
| 5.0 | Apr 7, 2026 | Professioneel rapport: hosted rapport (Supabase Storage + Netlify proxy), email summary, LinkedIn mockup PNG (Pillow), storage uploads, Supabase schema update |
| 5.1 | Apr 7, 2026 | Figma designs: 8 pages — ProfielScore (4), Kandidatentekort (2), Recruitment APK (2) in file 5mWJIMDO3NQwfN2wls8LoS |

---

## Figma Design Reference

**Figma file:** `5mWJIMDO3NQwfN2wls8LoS`
**URL:** https://www.figma.com/design/5mWJIMDO3NQwfN2wls8LoS/

| Page | Node ID | Inhoud |
|------|---------|--------|
| Page | Node ID | Product | Inhoud |
|------|---------|---------|--------|
| Landing Page | `0:1` | ProfielScore | Live profielscore.nl capture (1890×3929) |
| Hosted Rapport | `19:2` | ProfielScore | Score hero, 10 category bars, 3 headlines, about, SEO pills, actieplan, mockup, CTA |
| LinkedIn Mockup | `19:3` | ProfielScore | LinkedIn-style profielkaart (1200×800), score overlay, voor/na, VERBETERD badges |
| Email Template | `19:4` | ProfielScore | 600px email: score cirkel, top 3, verbeterpunten, headline, CTA |
| KT — Vacature Rapport | `28:2` | Kandidatentekort | Vacature score, 8 categorieën, marktanalyse, salaris benchmark, herschreven tekst, kanaaladvies |
| KT — Email Template | `28:3` | Kandidatentekort | Score, bevindingen (groen/oranje/rood), markt snapshot, quick wins, CTA |
| APK — Audit Rapport | `28:4` | Recruitment APK | APK score, 8 audit categorieën, benchmark tabel, ROI berekening, 4-fasen implementatieplan, diensten |
| APK — Email Template | `28:5` | Recruitment APK | Score, kritieke verbeterpunten, €47K besparing, quick wins, vervolggesprek CTA |

### Brand Tokens per Product

| Product | Stijl | Primary | Accent | Background | Text |
|---------|-------|---------|--------|------------|------|
| **ProfielScore** | Dark neon | `#FF5500` orange | `#ff00cc` magenta | `#07050f` dark violet | `#f2eeff` light |
| **Kandidatentekort** | Light professional | `#2563EB` blue | `#16A34A` green | `#FAFAFC` light gray | `#111827` dark |
| **Recruitment APK** | Corporate formal | `#1E40AF` navy blue | `#CA8A04` gold | `#F8F9FB` off-white | `#0F172A` navy |

---

## Cross-Product Rapport Architectuur

De ProfielScore rapport-stack is herbruikbaar voor andere Recruitin producten. Hieronder de architectuur en hoe je het toepast op **kandidatentekort.nl** en **Recruitment APK**.

### Gedeelde Stack (herbruikbaar)

```
Shared Components (kopieer en pas aan):
├── generator/storage_uploader.py      → Upload naar Supabase Storage (bucket per product)
├── generator/report_builder.py        → Jinja2 renderer (templates wisselen per product)
├── generator/templates/*.html         → Jinja2 templates (rapport + email)
├── netlify/functions/rapport.js       → Proxy: Supabase → text/html (1 function per product)
└── Resend API                         → Email delivery
```

### Toepassing op Kandidatentekort.nl

**Product:** Vacature-analyse rapport voor werkgevers
**Locatie:** `/Users/wouterarts/projects/Recruitin/kandidatentekort/kandidatentekort-automation-github/`

```
Kandidatentekort Rapport Architectuur:
├── Input: Jotform vacature intake → Claude Haiku analyse
├── Rapport (hosted):
│   ├── Vacature Score (0-100): vindbaarheid, aantrekkelijkheid, concurrentiekracht
│   ├── Marktanalyse: aantal kandidaten, concurrerende vacatures, schaarste-indicator
│   ├── Salaris benchmark: marktconform vs. aangeboden
│   ├── Verbeterpunten: vacaturetekst, kanalen, employer branding
│   ├── Herschreven vacaturetekst (AI-generated)
│   └── Actieplan (genummerd)
├── Email summary: score + top 3 verbeterpunten + CTA → hosted rapport
├── Storage: Supabase bucket "kandidatentekort-assets"
│   └── {YYYYMMDD}/{bedrijfsnaam}/rapport.html
└── Proxy: kandidatentekort.nl/.netlify/functions/rapport
```

**Implementatie stappen:**
1. Kopieer `generator/storage_uploader.py` → pas bucket aan naar `kandidatentekort-assets`
2. Maak Jinja2 templates: `kt_hosted_rapport.html` + `kt_email_rapport.html`
3. Gebruik kandidatentekort brand (lichtere kleuren, professionele look)
4. Voeg `rapport.js` toe aan kandidatentekort Netlify functions
5. Update `kandidatentekort-automation/main.py`: na Claude analyse → render rapport → upload → email
6. Supabase: voeg `rapport_url` kolom toe aan relevante tabel

### Toepassing op Recruitment APK

**Product:** Recruitment proces audit rapport voor HR-afdelingen
**Pipeline:** Pipedrive pipeline `id=2` (Recruitment APK)

```
Recruitment APK Rapport Architectuur:
├── Input: Intake gesprek data → gestructureerde audit
├── Rapport (hosted):
│   ├── APK Score (0-100): proces, kanalen, employer brand, candidate experience, data
│   ├── Benchmark: vergelijking met best practices
│   ├── Per categorie: score + feedback + concrete verbeteringen
│   ├── ROI berekening: kosten huidige proces vs. geoptimaliseerd
│   ├── Implementatieplan (gefaseerd, met tijdlijn)
│   └── Recruitin diensten die passen bij gaps
├── Email summary: APK score + top issues + CTA → hosted rapport
├── Storage: Supabase bucket "recruitment-apk-assets"
│   └── {YYYYMMDD}/{bedrijfsnaam}/apk-rapport.html
└── Proxy: aparte Netlify function of zelfde site
```

**Implementatie stappen:**
1. Ontwerp APK-specifieke Jinja2 templates (professioneel, wit/blauw, corporate)
2. Bouw scoring engine voor recruitment proces categorieën
3. Kopieer storage_uploader.py → pas bucket aan
4. Integreer met Pipedrive: deal stage → trigger rapport generatie
5. Resend email met samenvatting + link naar volledig rapport

### Template Design Principes (alle producten)

| Principe | Hoe |
|----------|-----|
| **Two-tier delivery** | Email = compact summary + CTA → hosted = volledig rapport |
| **Email-safe HTML** | Table-based layout, inline styles, geen CSS vars/flexbox/grid |
| **Hosted rapport** | Standalone HTML, alle CSS inline, print-to-PDF via `window.print()` |
| **Storage** | Supabase Storage (public bucket), Netlify proxy voor text/html |
| **Copy-to-clipboard** | JS `navigator.clipboard.writeText()` voor teksten die gebruiker moet overnemen |
| **Branding** | Per product eigen kleurenpalet, maar zelfde layout patronen |
| **Scoring visual** | Conic-gradient ring (CSS) voor hoofdscore, kleur-bars voor categorieën |
