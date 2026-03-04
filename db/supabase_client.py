"""
Supabase client module voor de LinkedIn Profile Optimizer Agent.
Handelt opslag en ophalen van lead data af.

Gebruik:
    from db.supabase_client import SupabaseClient
    db = SupabaseClient()
    lead = db.create_lead(form1_data)
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from supabase import create_client, Client
except ImportError:
    print("⚠️  supabase-py niet geïnstalleerd. Voer uit: pip install supabase")
    raise


class SupabaseClient:
    """Client voor Supabase database operaties."""

    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "https://jdistoacicmzdazdaubh.supabase.co")
        self.key = os.environ.get("SUPABASE_ANON_KEY", "")
        
        if not self.key:
            raise ValueError("SUPABASE_ANON_KEY is niet geconfigureerd in .env")
        
        self.client: Client = create_client(self.url, self.key)
        self.table = self.client.table("leads")

    # ==========================================
    # Form 1: Lead aanmaken
    # ==========================================
    def create_lead(self, form1_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maakt een nieuwe lead aan vanuit Form 1 data."""
        lead = {
            "first_name": form1_data.get("first_name", ""),
            "last_name": form1_data.get("last_name", ""),
            "email": form1_data.get("email", ""),
            "linkedin_url": form1_data.get("linkedin_url", ""),
            "linkedin_goal": form1_data.get("linkedin_goal", ""),
            "wants_banner": form1_data.get("wants_banner", True),
            "privacy_consent": True,
            "status": "pending",
            "jotform_submission_id": form1_data.get("submission_id", ""),
        }

        result = self.table.insert(lead).execute()
        return result.data[0] if result.data else {}

    # ==========================================
    # Status updates
    # ==========================================
    def update_status(self, lead_id: str, status: str) -> None:
        """Update de verwerkingsstatus van een lead."""
        self.table.update({"status": status}).eq("id", lead_id).execute()

    # ==========================================
    # LinkedIn scraped data opslaan
    # ==========================================
    def save_scraped_data(self, lead_id: str, scraped: Dict[str, Any]) -> None:
        """Sla scraped LinkedIn data op."""
        update = {
            "scraped_headline": scraped.get("headline", ""),
            "scraped_about": scraped.get("about", ""),
            "scraped_job_title": scraped.get("job_title", ""),
            "scraped_employer": scraped.get("employer", ""),
            "scraped_location": scraped.get("location", ""),
            "scraped_experience": json.dumps(scraped.get("experience", [])),
            "scraped_skills": json.dumps(scraped.get("skills", [])),
            "scraped_education": json.dumps(scraped.get("education", [])),
            "scraped_profile_photo_url": scraped.get("profile_photo_url", ""),
            "scraped_raw": json.dumps(scraped),
            "status": "analyzing",
        }
        self.table.update(update).eq("id", lead_id).execute()

    def needs_form2(self, lead_id: str) -> bool:
        """Check of er genoeg data is, of dat Form 2 nodig is."""
        result = self.table.select("*").eq("id", lead_id).execute()
        if not result.data:
            return True

        lead = result.data[0]
        # Minimum data: headline + about + job_title
        has_headline = bool(lead.get("scraped_headline"))
        has_about = bool(lead.get("scraped_about"))
        has_job = bool(lead.get("scraped_job_title"))

        return not (has_headline and has_about and has_job)

    # ==========================================
    # Form 2: Aanvullende data opslaan
    # ==========================================
    def save_form2_data(self, lead_id: str, form2_data: Dict[str, Any]) -> None:
        """Sla Form 2 (aanvullende) data op."""
        update = {
            "form2_submitted": True,
            "form2_headline": form2_data.get("current_headline", ""),
            "form2_about": form2_data.get("current_about", ""),
            "form2_job_title": form2_data.get("current_job_title", ""),
            "form2_employer": form2_data.get("current_employer", ""),
            "form2_years_experience": form2_data.get("years_experience", ""),
            "form2_job_description": form2_data.get("current_job_description", ""),
            "form2_top_skills": form2_data.get("top_3_skills", ""),
            "form2_unique_value": form2_data.get("unique_value", ""),
            "form2_target_sector": form2_data.get("target_sector", ""),
            "form2_target_audience": form2_data.get("target_audience", ""),
            "form2_profile_photo_url": form2_data.get("profile_photo_url", ""),
            "form2_banner_style": form2_data.get("banner_style", ""),
            "form2_banner_color": form2_data.get("banner_color", ""),
            "jotform_form2_submission_id": form2_data.get("submission_id", ""),
            "status": "analyzing",
        }
        self.table.update(update).eq("id", lead_id).execute()

    # ==========================================
    # Analyse resultaten opslaan
    # ==========================================
    def save_analysis(self, lead_id: str, score: int, grade: str,
                      analysis_result: Dict, report_html: str = "",
                      mockup_html: str = "", banner_url: str = "") -> None:
        """Sla analyse resultaten op."""
        update = {
            "analysis_score": score,
            "analysis_grade": grade,
            "analysis_result": json.dumps(analysis_result),
            "report_html": report_html,
            "mockup_html": mockup_html,
            "banner_url": banner_url,
            "status": "completed",
        }
        self.table.update(update).eq("id", lead_id).execute()

    # ==========================================
    # Opzoeken
    # ==========================================
    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Haal een lead op via ID."""
        result = self.table.select("*").eq("id", lead_id).execute()
        return result.data[0] if result.data else None

    def get_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Haal een lead op via email."""
        result = self.table.select("*").eq("email", email).order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None

    def get_pending_leads(self) -> list:
        """Haal alle leads op die nog verwerkt moeten worden."""
        result = self.table.select("*").in_("status", ["pending", "analyzing"]).execute()
        return result.data or []

    # ==========================================
    # Delivery tracking
    # ==========================================
    def mark_sent(self, lead_id: str, email_id: str = "") -> None:
        """Markeer dat het rapport verzonden is."""
        self.table.update({
            "report_sent_at": datetime.utcnow().isoformat(),
            "report_email_id": email_id,
        }).eq("id", lead_id).execute()

    # ==========================================
    # Merged profiel data (scraped + form2)
    # ==========================================
    def get_merged_profile(self, lead_id: str) -> Dict[str, Any]:
        """Geeft een samengevoegd profiel: scraped data + form2 data.
        Form2 data overschrijft scraped data waar aanwezig."""
        lead = self.get_lead(lead_id)
        if not lead:
            return {}

        return {
            "first_name": lead.get("first_name", ""),
            "last_name": lead.get("last_name", ""),
            "email": lead.get("email", ""),
            "linkedin_url": lead.get("linkedin_url", ""),
            "linkedin_goal": lead.get("linkedin_goal", ""),
            "wants_banner": lead.get("wants_banner", True),
            # Prefer form2 data over scraped data
            "headline": lead.get("form2_headline") or lead.get("scraped_headline", ""),
            "about": lead.get("form2_about") or lead.get("scraped_about", ""),
            "job_title": lead.get("form2_job_title") or lead.get("scraped_job_title", ""),
            "employer": lead.get("form2_employer") or lead.get("scraped_employer", ""),
            "location": lead.get("scraped_location", ""),
            "years_experience": lead.get("form2_years_experience", ""),
            "job_description": lead.get("form2_job_description", ""),
            "top_skills": lead.get("form2_top_skills", ""),
            "unique_value": lead.get("form2_unique_value", ""),
            "target_sector": lead.get("form2_target_sector", ""),
            "target_audience": lead.get("form2_target_audience", ""),
            "banner_style": lead.get("form2_banner_style", ""),
            "banner_color": lead.get("form2_banner_color", ""),
            "profile_photo_url": lead.get("form2_profile_photo_url") or lead.get("scraped_profile_photo_url", ""),
            "experience": json.loads(lead.get("scraped_experience", "[]") or "[]"),
            "skills": json.loads(lead.get("scraped_skills", "[]") or "[]"),
            "education": json.loads(lead.get("scraped_education", "[]") or "[]"),
        }


if __name__ == "__main__":
    print("Supabase client — gebruik: from db.supabase_client import SupabaseClient")
    print("Voer eerst supabase/schema.sql uit in je Supabase SQL editor.")
