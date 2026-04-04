"""
Webhook Handler — FastAPI endpoint voor JotForm submissions.
Ontvangt JotForm webhook POSTs en triggert de analyse pipeline.

Flow:
    1. Landing page → Form 1 (quick: URL + email)
    2. JotForm Form 1 → Webhook → Clay enrichment
    3. Clay callback → Check data completeness
    4a. Genoeg data → run_analysis pipeline → email rapport
    4b. Te weinig data → email link naar Form 2 (uitgebreid)
    5. Form 2 webhook → run_analysis pipeline → email rapport
"""

import os
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from models import ProfileIntake
from run_analysis import run_full_analysis
from db.clay_client import ClayEnrichment
from db.lemlist_client import LemlistClient
from db.pipedrive_client import PipedriveClient

load_dotenv()

# Try Supabase (optional, graceful fallback)
try:
    from db.supabase_client import SupabaseClient
    db = SupabaseClient()
    print("✅ Supabase verbonden")
except Exception as e:
    db = None
    print(f"⚠️  Supabase niet beschikbaar: {e}")

# Init clients
lemlist = LemlistClient()
pipedrive = PipedriveClient()

# ============================================================
# FORM IDs
# ============================================================
FORM1_ID = os.environ.get("JOTFORM_FORM_ID", "260606272965058")      # Quick signup
FORM2_ID = os.environ.get("JOTFORM_FORM2_ID", "260626168675062")     # Uitgebreide intake
FORM2_URL = f"https://form.jotform.com/{FORM2_ID}"

app = FastAPI(
    title="LinkedIn Profile Optimizer Agent",
    version="2.1.0",
    description="Webhook endpoint voor JotForm LinkedIn profiel intake"
)


# ============================================================
# JOTFORM FIELD MAPPING — FORM 1 (Quick Signup)
# ============================================================
# Form 1 velden (260606272965058):
#   2 = Volledige naam (control_fullname)
#   3 = E-mailadres (control_email)
#  46 = LinkedIn Profiel URL (control_textbox)

def map_form1_submission(answers: dict) -> dict:
    """Mapt Form 1 (quick signup) naar minimum data voor Clay enrichment."""
    def get_answer(qid: str, default: str = "") -> str:
        answer = answers.get(qid, {})
        if isinstance(answer, dict):
            # Fullname veld geeft first/last terug
            if answer.get("type") == "control_fullname" or "first" in answer.get("answer", {}).__class__.__name__:
                parts = answer.get("answer", {})
                if isinstance(parts, dict):
                    return f"{parts.get('first', '')} {parts.get('last', '')}".strip()
            return answer.get("answer", answer.get("prettyFormat", answer.get("text", default)))
        return str(answer) if answer else default

    name = get_answer("2", "Lead")
    name_parts = name.split(" ", 1)

    return {
        "first_name": name_parts[0] if name_parts else "Lead",
        "last_name": name_parts[1] if len(name_parts) > 1 else "",
        "email": get_answer("3", ""),
        "linkedin_url": get_answer("46", ""),
    }


# ============================================================
# JOTFORM FIELD MAPPING — FORM 2 (Uitgebreide Intake)
# ============================================================
# Form 2 velden (260626168675062):
#   4  = Volledige naam         →  first_name + last_name
#   5  = E-mailadres            →  email
#   6  = Telefoonnummer         →  phone
#   7  = Woonplaats + Provincie →  location
#   9  = LinkedIn profiel URL   →  linkedin_url
#  10  = Huidige headline       →  current_headline
#  11  = Huidige 'Over mij'     →  current_about
#  12  = Banner vraag           →  has_banner
#  14  = Huidige functietitel   →  current_job_title
#  15  = Huidige werkgever      →  current_employer
#  16  = Type dienstverband     →  employment_type
#  17  = Jaren werkervaring     →  years_experience
#  18  = Startdatum functie     →  current_job_start
#  19  = Functie beschrijving   →  current_job_description
#  20  = Eerdere werkervaring   →  previous_experience
#  22  = LinkedIn doel          →  linkedin_goal
#  23  = Sector/branche         →  target_sector
#  24  = Doelgroep              →  target_audience
#  25  = Top 3 vaardigheden     →  top_3_skills
#  26  = Onderscheidend         →  unique_value
#  28  = Opleidingen            →  education
#  29  = Certificaten           →  certificates
#  30  = Vaardigheden           →  current_skills
#  32  = Banner stijl           →  banner_style
#  33  = Banner kleur           →  banner_color_preference
#  34  = Banner tekst           →  banner_text_preference

def map_form2_submission(answers: dict) -> ProfileIntake:
    """Mapt Form 2 (uitgebreide intake) naar een ProfileIntake model."""

    def get_answer(qid: str, default: str = "") -> str:
        answer = answers.get(qid, {})
        if isinstance(answer, dict):
            # Fullname veld
            if "first" in str(answer.get("answer", "")):
                parts = answer.get("answer", {})
                if isinstance(parts, dict):
                    return f"{parts.get('first', '')} {parts.get('last', '')}".strip()
            return answer.get("answer", answer.get("prettyFormat", answer.get("text", default)))
        return str(answer) if answer else default

    name = get_answer("4", "Lead")
    name_parts = name.split(" ", 1)

    # Checkbox veld (34) kan meerdere waarden bevatten
    banner_text_raw = get_answer("34", "")
    banner_text_list = [s.strip() for s in banner_text_raw.split("\n") if s.strip()] if banner_text_raw else None

    return ProfileIntake(
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        email=get_answer("5", ""),
        phone=get_answer("6", ""),
        location=get_answer("7", ""),

        linkedin_url=get_answer("9", ""),
        current_headline=get_answer("10", ""),
        current_about=get_answer("11", "geen"),
        has_banner=get_answer("12", "Nee, ik heb de standaard achtergrond"),

        current_job_title=get_answer("14", ""),
        current_employer=get_answer("15", ""),
        employment_type=get_answer("16", "Fulltime"),
        years_experience=get_answer("17", "6-10 jaar"),
        current_job_start=get_answer("18", ""),
        current_job_description=get_answer("19", ""),
        previous_experience=get_answer("20"),

        linkedin_goal=get_answer("22", "Een nieuwe baan vinden"),
        target_sector=get_answer("23", "Techniek & Industrie"),
        target_audience=get_answer("24", ""),
        top_3_skills=get_answer("25", ""),
        unique_value=get_answer("26", ""),

        education=get_answer("28", ""),
        certificates=get_answer("29"),
        current_skills=get_answer("30", ""),

        banner_style=get_answer("32", "Modern & Professioneel (strakke lijnen, zakelijk)"),
        banner_color_preference=get_answer("33", "Laat de agent kiezen op basis van mijn sector"),
        banner_text_preference=banner_text_list,
    )


# ============================================================
# HELPER: Determine which form submitted
# ============================================================

def detect_form_id(raw_data: dict) -> str:
    """Detecteer welk formulier de webhook triggerde."""
    return raw_data.get("formID", raw_data.get("form_id", ""))


def has_enough_data_for_analysis(clay_data: dict) -> bool:
    """Check of Clay voldoende data heeft opgehaald voor een analyse."""
    required = ["headline", "about", "job_title", "employer"]
    filled = sum(1 for k in required if clay_data.get(k))
    return filled >= 3  # Minimaal 3 van 4 velden moeten gevuld zijn


# ============================================================
# DELIVERY: Lemlist + Pipedrive + Supabase
# ============================================================

def deliver_report(
    email: str,
    name: str,
    linkedin_url: str,
    score: int,
    grade: str,
    report_path: str = None,
    banner_path: str = None,
    lead_id: str = None,
):
    """Levert het rapport af via Lemlist en pushed qualified leads naar Pipedrive.

    1. Voeg lead toe aan Lemlist campaign (rapport email)
    2. Als qualified → maak Pipedrive deal
    3. Sla resultaat op in Supabase
    """
    first_name = name.split(" ")[0]
    last_name = " ".join(name.split(" ")[1:]) if " " in name else ""

    # 1. Lemlist: voeg toe aan rapport-campaign
    print(f"\n📧 Lemlist: rapport versturen naar {email}")
    lemlist.add_lead_to_campaign(
        campaign_id=os.environ.get("LEMLIST_CAMPAIGN_ID", ""),
        email=email,
        first_name=first_name,
        last_name=last_name,
        linkedin_url=linkedin_url,
        score=score,
        grade=grade,
        report_url=report_path or "",
        banner_url=banner_path or "",
    )

    # 2. Pipedrive: qualified leads → deal
    if pipedrive.is_qualified(score):
        print(f"🏆 Qualified lead → Pipedrive")
        pipedrive.create_qualified_lead(
            name=name,
            email=email,
            linkedin_url=linkedin_url,
            score=score,
            grade=grade,
        )
    else:
        print(f"ℹ️  Score {score} < {pipedrive.qualified_threshold} → niet qualified")

    # 3. Supabase: resultaat opslaan
    if db and lead_id:
        try:
            db.save_analysis(
                lead_id=lead_id,
                score=score,
                grade=grade,
                analysis_result={"report_path": report_path, "banner_path": banner_path},
                banner_url=banner_path or "",
            )
            db.mark_sent(lead_id)
        except Exception as e:
            print(f"⚠️  Supabase opslaan mislukt: {e}")


def send_intake_form_email(email: str, name: str):
    """Stuur een email met link naar Form 2 via Resend."""
    print(f"📧 Intake formulier email sturen naar {email}")
    try:
        import resend
        resend.api_key = os.environ.get("RESEND_API_KEY", "")
        if resend.api_key:
            resend.Emails.send({
                "from": os.environ.get("EMAIL_FROM", "Recruitin <noreply@recruitin.nl>"),
                "to": email,
                "subject": "We hebben meer info nodig voor je LinkedIn rapport",
                "html": f"""
                <p>Hoi {name.split(' ')[0]},</p>
                <p>Bedankt voor je aanvraag! We konden niet genoeg informatie van je LinkedIn profiel halen
                om een volledig rapport te maken.</p>
                <p>Vul alsjeblieft <a href="{FORM2_URL}">dit korte formulier</a> in (5 min),
                dan maken we je persoonlijke rapport.</p>
                <p>Groet,<br>Team Recruitin</p>
                """,
            })
            print(f"   ✅ Email verstuurd naar {email}")
        else:
            print(f"   ⚠️ RESEND_API_KEY niet ingesteld")
    except Exception as e:
        print(f"   ❌ Email fout: {e}")


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
async def health_check():
    return {
        "status": "running",
        "agent": "LinkedIn Profile Optimizer v2.1",
        "forms": {
            "quick_signup": FORM1_ID,
            "extended_intake": FORM2_ID,
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook/jotform")
async def handle_jotform_webhook(request: Request):
    """
    Ontvangt JotForm webhook POST van BEIDE formulieren.

    Form 1 (quick signup): Start Clay enrichment
    Form 2 (uitgebreide intake): Direct naar analyse pipeline
    """
    try:
        # Parse incoming data
        try:
            raw_data = await request.json()
        except Exception:
            form_data = await request.form()
            raw_data = dict(form_data)
            if "rawRequest" in raw_data:
                raw_data = json.loads(raw_data["rawRequest"])

        form_id = detect_form_id(raw_data)
        answers = raw_data.get("answers", raw_data)
        timestamp = datetime.now().isoformat()

        print(f"\n{'='*60}")
        print(f"📨 Nieuwe JotForm submission: {timestamp}")
        print(f"   Form ID: {form_id}")
        print(f"{'='*60}")

        # ── FORM 1: Quick Signup ──────────────────────────
        if form_id == FORM1_ID or "46" in answers:
            lead_data = map_form1_submission(answers)
            print(f"   📋 Form 1 (Quick Signup)")
            print(f"   👤 {lead_data['first_name']} {lead_data['last_name']}")
            print(f"   📧 {lead_data['email']}")
            print(f"   🔗 {lead_data['linkedin_url']}")

            # Opslaan in Supabase
            lead_id = None
            if db:
                try:
                    result = db.create_lead(lead_data)
                    lead_id = result.get("id")
                    print(f"   💾 Supabase lead: {lead_id}")
                except Exception as e:
                    print(f"   ⚠️ Supabase: {e}")

            # Start Clay enrichment
            clay = ClayEnrichment()
            if not lead_id:
                lead_id = f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            enrichment_started = clay.enrich_linkedin_url(
                lead_id=lead_id,
                linkedin_url=lead_data["linkedin_url"],
                email=lead_data["email"],
                name=f"{lead_data['first_name']} {lead_data['last_name']}",
            )

            if not enrichment_started:
                # Clay niet geconfigureerd → stuur direct intake form link
                print("   ⚠️ Clay niet beschikbaar, stuur intake formulier")
                send_intake_form_email(lead_data["email"], lead_data["first_name"])

            return JSONResponse(content={
                "status": "success",
                "action": "clay_enrichment_started" if enrichment_started else "intake_form_sent",
                "lead_id": lead_id,
                "message": "Enrichment gestart, wacht op Clay callback" if enrichment_started
                           else "Intake formulier email verstuurd",
            })

        # ── FORM 2: Uitgebreide Intake ────────────────────
        elif form_id == FORM2_ID or "10" in answers:
            print(f"   📋 Form 2 (Uitgebreide Intake)")
            intake = map_form2_submission(answers)
            print(f"   👤 {intake.full_name} ({intake.email})")

            # Direct naar analyse pipeline
            analysis = run_full_analysis(intake)

            # Deliver: Lemlist + Pipedrive + Supabase
            deliver_report(
                email=intake.email,
                name=intake.full_name,
                linkedin_url=intake.linkedin_url,
                score=analysis.score.total_score,
                grade=analysis.score.grade,
                report_path=analysis.report_pdf_path,
                banner_path=analysis.banner_png_path,
            )

            return JSONResponse(content={
                "status": "success",
                "action": "analysis_complete",
                "lead_name": intake.full_name,
                "score": analysis.score.total_score,
                "grade": analysis.score.grade,
                "report_path": analysis.report_pdf_path,
                "banner_path": analysis.banner_png_path,
            })

        else:
            print(f"   ⚠️ Onbekend formulier: {form_id}")
            return JSONResponse(content={"status": "error", "message": "Onbekend formulier"}, status_code=400)

    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/clay-callback")
async def handle_clay_callback(request: Request):
    """
    Ontvangt Clay enrichment resultaat.

    Na enrichment:
    - Als genoeg data → run analyse pipeline
    - Als te weinig data → stuur email met link naar Form 2
    """
    try:
        clay_data = await request.json()
        print(f"\n📨 Clay callback ontvangen: {datetime.now().isoformat()}")

        # Parse Clay response
        clay = ClayEnrichment()
        enriched = clay.parse_clay_response(clay_data)

        lead_email = clay_data.get("email", "")
        lead_name = clay_data.get("name", "Lead")
        linkedin_url = clay_data.get("linkedin_url", "")

        print(f"   👤 {lead_name} ({lead_email})")
        print(f"   📊 Data: headline={bool(enriched['headline'])}, "
              f"about={bool(enriched['about'])}, "
              f"job={bool(enriched['job_title'])}, "
              f"employer={bool(enriched['employer'])}")

        if has_enough_data_for_analysis(enriched):
            print("   ✅ Genoeg data voor analyse!")

            # Bouw ProfileIntake van Clay data
            name_parts = lead_name.split(" ", 1)
            intake = ProfileIntake(
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else "",
                email=lead_email,
                linkedin_url=linkedin_url,
                location=enriched.get("location", ""),
                current_headline=enriched.get("headline", ""),
                current_about=enriched.get("about", "geen"),
                current_job_title=enriched.get("job_title", ""),
                current_employer=enriched.get("employer", ""),
                profile_photo_url=enriched.get("profile_photo_url"),
            )

            analysis = run_full_analysis(intake)

            # Deliver: Lemlist + Pipedrive + Supabase
            deliver_report(
                email=lead_email,
                name=lead_name,
                linkedin_url=linkedin_url,
                score=analysis.score.total_score,
                grade=analysis.score.grade,
                report_path=analysis.report_pdf_path,
                banner_path=analysis.banner_png_path,
            )

            return JSONResponse(content={
                "status": "success",
                "action": "analysis_complete",
                "score": analysis.score.total_score,
            })

        else:
            print("   ❌ Te weinig data, stuur intake formulier")
            send_intake_form_email(lead_email, lead_name)

            return JSONResponse(content={
                "status": "success",
                "action": "intake_form_sent",
                "message": "Niet genoeg data, intake formulier verstuurd",
            })

    except Exception as e:
        print(f"❌ Clay Callback Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_profile(intake_data: dict):
    """
    Direct analyse endpoint (voor testen zonder JotForm).
    Accepteert een JSON body met ProfileIntake velden.
    """
    try:
        intake = ProfileIntake(**intake_data)
        analysis = run_full_analysis(intake)

        return JSONResponse(content={
            "status": "success",
            "lead_name": intake.full_name,
            "score": analysis.score.total_score,
            "grade": analysis.score.grade,
            "report_path": analysis.report_pdf_path,
            "mockup_path": analysis.mockup_html_path,
            "banner_path": analysis.banner_png_path,
            "headline_options": [
                {"style": h.style, "text": h.text}
                for h in analysis.headline_options
            ],
            "seo_keywords": [
                {"keyword": k.keyword, "relevance": k.relevance_score}
                for k in analysis.seo_keywords
            ],
            "action_items": analysis.action_items,
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/profielscore-submit")
async def profielscore_submit(request: Request):
    """
    Automatische flow voor profielscore.nl form submissions.
    Aangeroepen (fire-and-forget) door de Netlify submit function.

    1. Ontvang minimale form data (naam, email, linkedin_url, bedrijf)
    2. Bouw ProfileIntake met defaults voor ontbrekende velden
    3. Run volledige analyse pipeline
    4. Stuur rapport email via Resend
    """
    try:
        data = await request.json()
        email = data.get("email", "")
        voornaam = data.get("voornaam", "")
        achternaam = data.get("achternaam", "")
        bedrijfsnaam = data.get("bedrijfsnaam", "")
        linkedin_url = data.get("linkedin_url", "")

        print(f"\n{'='*60}")
        print(f"📨 ProfielScore submit: {email} ({linkedin_url})")
        print(f"{'='*60}")

        # Bouw ProfileIntake met beschikbare data + sectordefaults
        intake = ProfileIntake(
            first_name=voornaam or "HR",
            last_name=achternaam or "Professional",
            email=email,
            location="Nederland",
            linkedin_url=linkedin_url,
            current_headline=f"Professional bij {bedrijfsnaam}" if bedrijfsnaam else "HR & Recruitment Professional",
            current_about="geen",
            current_job_title="HR / Recruitment Professional",
            current_employer=bedrijfsnaam or "Onbekend",
            linkedin_goal="Meer klanten / opdrachten krijgen",
            target_sector="HR & Recruitment",
            target_audience="HR-managers en directeuren bij technische bedrijven",
            top_3_skills="Recruitment, Werving & Selectie, Employer Branding",
            current_skills="Recruitment, Headhunting, LinkedIn Recruiter, Employer Branding",
            banner_style="Modern & Professioneel",
            banner_color_preference="Laat de agent kiezen",
        )

        # Run analyse
        analysis = run_full_analysis(intake)
        score = analysis.score.total_score
        grade = analysis.score.grade
        naam = intake.full_name
        first = voornaam or naam.split(" ")[0]

        print(f"   ✅ Analyse klaar: {score}/100 (Grade {grade})")

        # Stuur rapport email via Resend
        resend_api_key = os.environ.get("RESEND_API_KEY") or "re_VFP9be65_JW7HUJDZV9Vzz4oSwpKANNaW"
        print(f"   🔑 Resend key aanwezig: {bool(resend_api_key)}")

        score_color = "#16a34a" if score >= 70 else "#d97706" if score >= 50 else "#dc2626"
        score_label = "Goed" if score >= 70 else "Verbetering mogelijk" if score >= 50 else "Verbetering nodig"

        headline_html = "".join([
            f'<div style="background:#f7f3ff;border-left:4px solid #7c3aed;padding:14px 16px;border-radius:0 8px 8px 0;margin-bottom:10px;">'
            f'<p style="margin:0 0 4px;font-size:11px;color:#7c3aed;font-weight:bold;text-transform:uppercase;">{h.style}</p>'
            f'<p style="margin:0;color:#1a1a2e;font-size:14px;">{h.text}</p></div>'
            for h in analysis.headline_options[:3]
        ])

        keywords_html = "".join([
            f'<span style="display:inline-block;background:#ede9fe;color:#6d28d9;padding:6px 12px;border-radius:20px;font-size:13px;margin:4px;">{k.keyword}</span>'
            for k in analysis.seo_keywords[:8]
        ])

        action_html = "".join([
            f'<div style="display:flex;align-items:flex-start;margin-bottom:12px;">'
            f'<span style="background:#7c3aed;color:#fff;border-radius:50%;min-width:24px;height:24px;line-height:24px;text-align:center;font-size:12px;font-weight:bold;margin-right:12px;">{i+1}</span>'
            f'<p style="margin:0;color:#374151;font-size:14px;line-height:1.5;padding-top:4px;">{item}</p></div>'
            for i, item in enumerate(analysis.action_items[:6])
        ])

        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;color:#1a1a2e;">
          <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:48px 40px;text-align:center;">
            <h1 style="color:#fff;margin:0 0 8px;font-size:32px;letter-spacing:-1px;">ProfielScore</h1>
            <p style="color:#a78bfa;margin:0;font-size:15px;">LinkedIn Profiel Analyse Rapport</p>
          </div>
          <div style="padding:40px;text-align:center;border-bottom:1px solid #f0f0f0;">
            <div style="display:inline-block;background:{score_color};border-radius:50%;width:100px;height:100px;line-height:100px;margin:0 auto;">
              <span style="color:#fff;font-size:42px;font-weight:bold;">{score}</span>
            </div>
            <p style="color:#6b7280;margin:8px 0 0;font-size:14px;">van de 100 punten</p>
            <p style="color:{score_color};font-size:18px;font-weight:bold;margin:8px 0 0;">{score_label} — Grade {grade}</p>
            <h2 style="color:#1a1a2e;margin:24px 0 8px;">Hoi {first},</h2>
            <p style="color:#4a5568;line-height:1.7;max-width:480px;margin:0 auto;">
              Je ProfielScore is <strong>{score}/100</strong>. Hieronder vind je je persoonlijke analyse met concrete verbeterpunten.
            </p>
          </div>
          <div style="padding:32px 40px;border-bottom:1px solid #f0f0f0;">
            <h3 style="color:#1a1a2e;margin:0 0 20px;">🎯 Aanbevolen Headline Opties</h3>
            {headline_html}
          </div>
          <div style="padding:32px 40px;border-bottom:1px solid #f0f0f0;">
            <h3 style="color:#1a1a2e;margin:0 0 16px;">🔍 Ontbrekende SEO Keywords</h3>
            <p style="color:#4a5568;font-size:14px;margin:0 0 16px;">Voeg deze keywords toe voor betere vindbaarheid:</p>
            <div>{keywords_html}</div>
          </div>
          <div style="padding:32px 40px;border-bottom:1px solid #f0f0f0;">
            <h3 style="color:#1a1a2e;margin:0 0 20px;">✅ Jouw Actieplan</h3>
            {action_html}
          </div>
          <div style="padding:40px;text-align:center;background:#fafafa;">
            <p style="color:#4a5568;margin:0 0 24px;">Vragen of hulp bij implementatie?</p>
            <a href="mailto:wouter.arts@recruitin.nl" style="display:inline-block;background:#7c3aed;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;">Neem contact op</a>
          </div>
          <div style="background:#1a1a2e;padding:24px;text-align:center;">
            <p style="color:#6b7280;font-size:12px;margin:0;">profielscore.nl — een dienst van Recruitin B.V. | Doesburg</p>
          </div>
        </div>
        """

        import urllib.request
        import json as json_lib

        resend_body = json_lib.dumps({
            "from": "ProfielScore <noreply@kandidatentekort.nl>",
            "to": [email],
            "subject": f"Je ProfielScore Rapport — {score}/100 (Grade {grade})",
            "html": html_body
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=resend_body,
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode()
            print(f"   ✅ Rapport email verstuurd: {resp_body}")

        return JSONResponse(content={
            "status": "success",
            "email": email,
            "score": score,
            "grade": grade,
        })

    except Exception as e:
        print(f"❌ ProfielScore Submit Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🚀 LinkedIn Profile Optimizer Agent v2.1")
    print(f"   Server starten op http://0.0.0.0:{port}")
    print(f"   Endpoints:")
    print(f"     POST /webhook/jotform        — JotForm submissions (Form 1 & 2)")
    print(f"     POST /webhook/clay-callback   — Clay enrichment callback")
    print(f"     POST /analyze                 — Direct analyse (testen)")
    print(f"     GET  /                        — Health check")
    print(f"\n   Form 1 (Quick): {FORM1_ID}")
    print(f"   Form 2 (Uitgebreid): {FORM2_ID}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
