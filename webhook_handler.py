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

# Service role client voor status updates (bypass RLS)
db_admin = None
try:
    from supabase import create_client
    _sr_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    _sr_url = os.environ.get("SUPABASE_URL", "")
    if _sr_key and _sr_url:
        db_admin = create_client(_sr_url, _sr_key)
        print("✅ Supabase admin (service role) verbonden")
except Exception as e:
    print(f"⚠️  Supabase admin niet beschikbaar: {e}")

# Init clients
lemlist = LemlistClient()
pipedrive = PipedriveClient()


def upload_to_supabase_storage(file_path: str, bucket: str = "profielscore-assets") -> str:
    """Upload bestand naar Supabase Storage, return public URL.
    Gebruikt SUPABASE_SERVICE_KEY voor schrijfrechten.
    Maakt bucket aan als deze niet bestaat.
    """
    if not file_path or not os.path.exists(file_path):
        return ""

    service_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    supabase_url = os.environ.get("SUPABASE_URL", "")
    if not service_key or not supabase_url:
        print("   ⚠️ Supabase Storage: SERVICE_KEY of URL ontbreekt")
        return ""

    try:
        from supabase import create_client
        storage_client = create_client(supabase_url, service_key)

        # Bucket aanmaken als die niet bestaat (idempotent)
        try:
            storage_client.storage.create_bucket(bucket, options={"public": True})
        except Exception:
            pass  # Bucket bestaat al

        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"{timestamp}_{filename}"

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        content_type = "image/png" if filename.endswith(".png") else "text/html"
        storage_client.storage.from_(bucket).upload(
            storage_path, file_bytes,
            {"content-type": content_type}
        )

        public_url = storage_client.storage.from_(bucket).get_public_url(storage_path)
        print(f"   ✅ Storage upload: {storage_path}")
        return public_url

    except Exception as e:
        print(f"   ⚠️ Storage upload fout: {e}")
        return ""

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
        linkedin_pdf_base64 = data.get("linkedin_pdf_base64", "")

        print(f"\n{'='*60}")
        print(f"📨 ProfielScore submit: {email} ({linkedin_url})")
        print(f"{'='*60}")

        # Parse LinkedIn PDF als die is meegestuurd
        pdf_fields = {}
        if linkedin_pdf_base64:
            try:
                import base64
                from analyzer.pdf_parser import (parse_linkedin_pdf, pdf_data_to_intake_fields,
                    detect_sector_from_profile, detect_goal_from_profile, detect_audience_from_profile)
                pdf_bytes = base64.b64decode(linkedin_pdf_base64)
                print(f"   📄 LinkedIn PDF ontvangen ({len(pdf_bytes) // 1024} KB), parsing...")
                pdf_data = parse_linkedin_pdf(pdf_bytes)
                pdf_fields = pdf_data_to_intake_fields(pdf_data)
                # Auto-detect sector, goal, audience from profile content
                detected_sector = detect_sector_from_profile(pdf_data)
                detected_goal = detect_goal_from_profile(pdf_data)
                detected_audience = detect_audience_from_profile(pdf_data, detected_sector)
                pdf_fields["target_sector"] = detected_sector
                pdf_fields["linkedin_goal"] = detected_goal
                pdf_fields["target_audience"] = detected_audience
                pdf_fields["top_3_skills"] = ", ".join(pdf_data.skills[:5]) if pdf_data.skills else ""
                print(f"   ✅ PDF parsed: {pdf_data.full_name} — {pdf_data.headline}")
                print(f"      Skills: {len(pdf_data.skills)}, Experience: {len(pdf_data.experiences)}, Education: {len(pdf_data.education)}")
                print(f"      Sector: {detected_sector}, Goal: {detected_goal}")
            except Exception as e:
                print(f"   ⚠️ PDF parsing mislukt: {e} — doorgaan met form data")

        # Update Supabase status → "analyzing"
        if db_admin:
            try:
                update_data = {"status": "analyzing"}
                if pdf_fields:
                    update_data["has_pdf"] = True
                db_admin.table("profielscore_leads").update(
                    update_data
                ).eq("email", email).execute()
                print(f"   💾 Status → analyzing")
            except Exception as e:
                print(f"   ⚠️ Supabase status update: {e}")

        # Bouw ProfileIntake: PDF data > form data > defaults
        intake = ProfileIntake(
            first_name=pdf_fields.get("first_name") or voornaam or "",
            last_name=pdf_fields.get("last_name") or achternaam or "",
            email=email,
            location=pdf_fields.get("location") or data.get("location", "Nederland"),
            linkedin_url=linkedin_url,
            current_headline=pdf_fields.get("current_headline") or data.get("current_headline") or (f"Professional bij {bedrijfsnaam}" if bedrijfsnaam else ""),
            current_about=pdf_fields.get("current_about") or data.get("current_about", "geen"),
            current_job_title=pdf_fields.get("current_job_title") or data.get("current_job_title", ""),
            current_employer=pdf_fields.get("current_employer") or data.get("current_employer", bedrijfsnaam or "Onbekend"),
            years_experience=pdf_fields.get("years_experience") or data.get("years_experience", ""),
            current_job_description=pdf_fields.get("current_job_description") or data.get("current_job_description", ""),
            previous_experience=pdf_fields.get("previous_experience") or data.get("previous_experience", ""),
            linkedin_goal=pdf_fields.get("linkedin_goal") or data.get("linkedin_goal", "Mijn personal brand versterken"),
            target_sector=pdf_fields.get("target_sector") or data.get("target_sector", ""),
            target_audience=pdf_fields.get("target_audience") or data.get("target_audience", ""),
            top_3_skills=pdf_fields.get("top_3_skills") or data.get("top_3_skills", ""),
            unique_value=data.get("unique_value", ""),
            education=pdf_fields.get("education") or data.get("education", ""),
            certificates=pdf_fields.get("certificates") or data.get("certificates", ""),
            current_skills=pdf_fields.get("current_skills") or data.get("current_skills", ""),
            banner_style=data.get("banner_style", "Modern & Professioneel"),
            banner_color_preference=data.get("banner_color_preference", "Laat de agent kiezen"),
        )

        # Run analyse
        analysis = run_full_analysis(intake)
        score = analysis.score.total_score
        grade = analysis.score.grade
        naam = intake.full_name
        first = voornaam or naam.split(" ")[0]

        print(f"   ✅ Analyse klaar: {score}/100 (Grade {grade})")

        # Stuur rapport email via Resend
        resend_api_key = os.environ.get("RESEND_API_KEY", "")
        if not resend_api_key:
            print("   ❌ RESEND_API_KEY niet geconfigureerd — rapport email overgeslagen")
            return JSONResponse(content={"status": "error", "message": "RESEND_API_KEY not configured"}, status_code=500)

        score_color = "#16a34a" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
        score_label = "Sterk profiel" if score >= 70 else "Ruimte voor groei" if score >= 50 else "Veel potentieel"

        # Score breakdown per categorie
        breakdown_html = ""
        for cat in analysis.score.categories:
            pct = int((cat.score / cat.max_score) * 100)
            bar_color = "#16a34a" if pct >= 70 else "#f59e0b" if pct >= 50 else "#ef4444"
            breakdown_html += (
                f'<tr>'
                f'<td style="padding:8px 0;font-size:13px;color:#374151;border-bottom:1px solid #f3f4f6;">{cat.name}</td>'
                f'<td style="padding:8px 0;border-bottom:1px solid #f3f4f6;width:50%;">'
                f'<div style="background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden;">'
                f'<div style="background:{bar_color};height:8px;width:{pct}%;border-radius:4px;"></div></div></td>'
                f'<td style="padding:8px 0 8px 12px;font-size:13px;font-weight:600;color:{bar_color};border-bottom:1px solid #f3f4f6;text-align:right;">{cat.score}/{cat.max_score}</td>'
                f'</tr>'
            )

        # Headline opties
        headline_html = ""
        for i, h in enumerate(analysis.headline_options[:3]):
            badge = '<span style="display:inline-block;background:#16a34a;color:#fff;font-size:10px;padding:2px 8px;border-radius:3px;margin-left:8px;vertical-align:middle;">AANBEVOLEN</span>' if i == 0 else ''
            headline_html += (
                f'<div style="background:#f8fafc;border:1px solid #e2e8f0;padding:16px;border-radius:8px;margin-bottom:10px;">'
                f'<p style="margin:0 0 6px;font-size:11px;color:#6366f1;font-weight:700;text-transform:uppercase;">{h.style}{badge}</p>'
                f'<p style="margin:0;color:#1e293b;font-size:15px;font-weight:500;">{h.text}</p></div>'
            )

        # Herschreven Over Mij sectie
        about_html = ""
        if analysis.improved_about and analysis.improved_about.full_text:
            about_text = analysis.improved_about.full_text.replace("\n", "<br>")
            about_html = f"""
            <div style="padding:32px 40px;border-bottom:1px solid #f0f0f0;">
              <h3 style="color:#1e293b;margin:0 0 8px;font-size:18px;">Herschreven 'Over Mij'</h3>
              <p style="color:#64748b;font-size:13px;margin:0 0 16px;">Kopieer deze tekst naar je LinkedIn profiel:</p>
              <div style="background:#f0fdf4;border:1px solid #bbf7d0;padding:20px;border-radius:8px;font-size:14px;color:#1e293b;line-height:1.7;">{about_text}</div>
            </div>"""

        # SEO keywords
        keywords_html = "".join([
            f'<span style="display:inline-block;background:#eef2ff;color:#4338ca;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;margin:3px;">{k.keyword}</span>'
            for k in analysis.seo_keywords[:8]
        ])

        # Actieplan
        action_html = ""
        for i, item in enumerate(analysis.action_items[:5]):
            action_html += (
                f'<div style="display:flex;align-items:flex-start;margin-bottom:14px;">'
                f'<div style="background:#6366f1;color:#fff;border-radius:50%;min-width:28px;height:28px;line-height:28px;text-align:center;font-size:13px;font-weight:700;margin-right:14px;flex-shrink:0;">{i+1}</div>'
                f'<p style="margin:0;color:#374151;font-size:14px;line-height:1.6;padding-top:4px;">{item}</p></div>'
            )

        html_body = f"""
        <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;color:#1e293b;background:#ffffff;">
          <!-- Header -->
          <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);padding:40px;text-align:center;">
            <h1 style="color:#fff;margin:0 0 4px;font-size:24px;font-weight:300;letter-spacing:2px;">PROFIELSCORE</h1>
            <p style="color:#94a3b8;margin:0;font-size:13px;">LinkedIn Profiel Analyse</p>
          </div>

          <!-- Score -->
          <div style="padding:40px;text-align:center;border-bottom:1px solid #f1f5f9;">
            <div style="display:inline-block;width:120px;height:120px;border-radius:50%;border:4px solid {score_color};line-height:120px;margin:0 auto;">
              <span style="color:{score_color};font-size:48px;font-weight:700;">{score}</span>
            </div>
            <p style="color:#64748b;margin:10px 0 0;font-size:13px;">van de 100 punten</p>
            <p style="color:{score_color};font-size:16px;font-weight:600;margin:6px 0 0;">{score_label}</p>
          </div>

          <!-- Intro -->
          <div style="padding:28px 40px;border-bottom:1px solid #f1f5f9;">
            <p style="color:#374151;line-height:1.7;margin:0;font-size:15px;">
              Hoi {first}, hieronder vind je jouw persoonlijke LinkedIn analyse met concrete verbeterpunten die je direct kunt toepassen.
            </p>
          </div>

          <!-- Score Breakdown -->
          <div style="padding:28px 40px;border-bottom:1px solid #f1f5f9;">
            <h3 style="color:#1e293b;margin:0 0 16px;font-size:16px;">Score per categorie</h3>
            <table style="width:100%;border-collapse:collapse;">{breakdown_html}</table>
          </div>

          <!-- Headlines -->
          <div style="padding:28px 40px;border-bottom:1px solid #f1f5f9;">
            <h3 style="color:#1e293b;margin:0 0 16px;font-size:16px;">Nieuwe headline opties</h3>
            <p style="color:#64748b;font-size:13px;margin:0 0 14px;">Huidige: <em style="color:#94a3b8;">{intake.current_headline[:80]}...</em></p>
            {headline_html}
          </div>

          <!-- About rewrite -->
          {about_html}

          <!-- SEO Keywords -->
          <div style="padding:28px 40px;border-bottom:1px solid #f1f5f9;">
            <h3 style="color:#1e293b;margin:0 0 8px;font-size:16px;">Ontbrekende SEO keywords</h3>
            <p style="color:#64748b;font-size:13px;margin:0 0 14px;">Verwerk deze in je headline, about en ervaring:</p>
            <div>{keywords_html}</div>
          </div>

          <!-- Actieplan -->
          <div style="padding:28px 40px;border-bottom:1px solid #f1f5f9;">
            <h3 style="color:#1e293b;margin:0 0 16px;font-size:16px;">Jouw actieplan</h3>
            {action_html}
          </div>

          <!-- CTA -->
          <div style="padding:36px 40px;text-align:center;background:#f8fafc;">
            <p style="color:#374151;margin:0 0 6px;font-size:15px;font-weight:600;">Hulp nodig bij de implementatie?</p>
            <p style="color:#64748b;margin:0 0 20px;font-size:13px;">We helpen je profiel optimaliseren zodat techtalent jou vindt.</p>
            <a href="mailto:wouter.arts@recruitin.nl" style="display:inline-block;background:#6366f1;color:#fff;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;">Plan een gesprek</a>
          </div>

          <!-- Footer -->
          <div style="padding:20px 40px;text-align:center;">
            <p style="color:#94a3b8;font-size:11px;margin:0;">profielscore.nl — Recruitin B.V. | Doesburg</p>
          </div>
        </div>
        """

        import resend as resend_lib
        resend_lib.api_key = resend_api_key
        send_result = resend_lib.Emails.send({
            "from": "ProfielScore <noreply@kandidatentekort.nl>",
            "to": [email],
            "subject": f"Je ProfielScore Rapport - {score}/100 (Grade {grade})",
            "html": html_body
        })
        print(f"   ✅ Rapport email verstuurd: {send_result}")

        # P6: Deliver to Lemlist + Pipedrive (qualified leads)
        try:
            deliver_report(
                email=email,
                name=naam,
                linkedin_url=linkedin_url,
                score=score,
                grade=grade,
                report_path="",  # rapport is inline email
                banner_path=banner_url,  # public URL i.p.v. lokaal pad
            )
        except Exception as e:
            print(f"   ⚠️ deliver_report fout (non-blocking): {e}")

        # P3: Update Supabase status → "completed"
        if db_admin:
            try:
                db_admin.table("profielscore_leads").update(
                    {"status": "completed"}
                ).eq("email", email).execute()
                print(f"   💾 Status → completed")
            except Exception as e:
                print(f"   ⚠️ Supabase status update: {e}")

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

        # P3: Update Supabase status → "failed"
        if db_admin:
            try:
                db_admin.table("profielscore_leads").update(
                    {"status": "failed"}
                ).eq("email", data.get("email", "")).execute()
            except Exception:
                pass

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
