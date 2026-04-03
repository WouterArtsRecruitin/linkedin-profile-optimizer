# ProfielScore Landing Page — Design & Architecture

**Project:** LinkedIn Profile Optimizer (ProfielScore)  
**Version:** 2.0 (High-Conversion Funnel Redesign — Apr 2026)  
**Live:** https://profielscore.nl  
**Deployed:** Netlify (auto-deploy on push main)

---

## Design Philosophy

The landing page follows a **trust-before-conversion** funnel that addresses a critical insight:

> Visitors come with skepticism. Asking them to fill a form before proving value fails. Build trust first → then convert.

**New Flow (Apr 2026):**
```
Hero (pain → hope) 
  ↓ 
Stats (social proof: 2.400+ analyses, 4.8★, +47% views)
  ↓ 
Before/After (visual proof of results: 42 → 87)
  ↓ 
Benefits (outcome-focused, not feature-focused)
  ↓ 
How It Works (demystify the process)
  ↓ 
Reviews (social proof from real users)
  ↓ 
Second CTA (re-engagement)
  ↓ 
Form (2-step, low friction)
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
**Hook:** `"Recruiters scrollen voorbij jou. Nog niet."`  
**Subhead:** `"Krijg gratis je LinkedIn ProfielScore — en zie precies wat je mist."`

**Content:**
- Hero blob (magenta, pulsing) on right side
- H1 + subhead (left side, z-index 2)
- **2-Step Form** (see Form section below)
- Score card mockup (visual trust signal)

**Height:** 700px min (desktop), 600px (tablet)

### 3. Stats Strip
**Purpose:** Inject social proof immediately after hero conviction.

**Layout:**
```
[2.400+]     [4.8★]          [+47%]
 analyses  gemiddelde beoordeling  meer weergaven
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

### 5. Benefits (Outcome-Focused)
**Heading:** `"Drie dingen die veranderen"`

**Cards (3-column grid):**
1. **"Zie waarom je gemist wordt"** — Score laat per onderdeel zien what recruiters see
2. **"Ontvang teksten die wél werken"** — Headline & About herschreven door AI
3. **"Val op in elke zoekopdracht"** — Keywords + banner = visibility

**Design:** Dark surface cards with magenta dot top indicator.

### 6. How It Works
**Purpose:** Demystify the process, reduce anxiety.

**Steps (3-column grid):**
1. **Plak je LinkedIn URL** — No password, no account access
2. **AI analyseert je profiel** — Compared to thousands of optimized examples
3. **Ontvang je rapport** — Within minutes in your inbox

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
- H2: "Klaar om meer recruiter contact te krijgen?"
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
[Telefoon]
[Doel: Meer views / Recruiter contact / Alles optimaliseren]
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
- **Score Card Animation** — Counts up from 0 → 69 on scroll into view, fills bar graphs

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

**Environment Variables:** (if needed for Netlify functions)
```
# Set in Netlify UI under Site Settings → Build & Deploy → Environment
```

---

## File Structure

```
landing-optimizer/
├── landing/
│   ├── index.html          ← Main landing page (1000+ lines)
│   ├── style.css           ← Neon design system (900+ lines)
│   ├── rapport-before.html ← Standalone rapport demo (BEFORE state)
│   ├── rapport-after.html  ← Standalone rapport demo (AFTER state)
│   └── rapport-dummy.html  ← Dummy rapport template
├── netlify/
│   └── functions/
│       └── submit.js       ← Form submission handler (to be created)
├── CLAUDE.md               ← This file
└── .netlify/
    └── toml                ← Netlify configuration (if needed)
```

---

## Next Steps (Backlog)

- [ ] **Netlify Function:** Create `netlify/functions/submit.js` to handle form submissions
  - Input: LinkedIn URL, email, optional fields
  - Output: Trigger analysis, send to Supabase + Lemlist + Jotform
  - Tracking: GA4, Meta Pixel, LinkedIn events

- [ ] **Supabase Integration:** Store leads in `profielscore_leads` table
  - Columns: email, linkedin_url, voornaam, achternaam, telefoonnummer, doel, created_at
  - RLS: Restrict public access

- [ ] **Lemlist Campaign:** Create automated sequence for leads
  - Campaign: `cam_profielscore_optimizer`
  - Sequence: Day 0 confirmation, Day 3 value email, Day 7 CTA, Day 14 breakup

- [ ] **Email Automation:** Send PDF rapport within 24h
  - Tool: Make.com or Zapier
  - Trigger: Form submission
  - Action: Generate rapport PDF, email to user

- [ ] **A/B Testing:** Test hook variations, CTA colors, form friction
  - Variant A: Current design
  - Variant B: Different hook ("Je LinkedIn profiel verdient beter")
  - Variant C: Form-first variant (test friction hypothesis)

- [ ] **Analytics Dashboard:** Track funnel metrics
  - Metrics: Visitors, hook impressions, form starts, form completes, conversion rate
  - Tools: GA4 + Data Studio

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

---

**Questions?** Check the git history or reach out.
