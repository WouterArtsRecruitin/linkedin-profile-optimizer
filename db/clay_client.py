"""
Clay enrichment client voor LinkedIn Profile Optimizer Agent.
Verstuurt LinkedIn URLs naar Clay voor profiel enrichment.

Clay werkt met webhooks:
1. Maak een Clay table aan met een webhook trigger
2. Stuur LinkedIn URL naar webhook
3. Clay enriched automatisch
4. Ontvang resultaat via webhook callback

Gebruik:
    from db.clay_client import ClayEnrichment
    clay = ClayEnrichment()
    clay.enrich_linkedin_url(lead_id, linkedin_url)
"""

import os
import requests
import json
from typing import Dict, Any, Optional


class ClayEnrichment:
    """Client voor Clay LinkedIn profile enrichment."""

    def __init__(self):
        self.api_key = os.environ.get("CLAY_API_KEY", "")
        self.webhook_url = os.environ.get("CLAY_WEBHOOK_URL", "")
        
        if not self.api_key:
            print("⚠️  CLAY_API_KEY niet geconfigureerd in .env")

    def enrich_linkedin_url(self, lead_id: str, linkedin_url: str,
                            email: str = "", name: str = "") -> bool:
        """Stuur een LinkedIn URL naar Clay voor enrichment.
        
        Args:
            lead_id: ID van de lead in Supabase
            linkedin_url: LinkedIn profiel URL
            email: E-mailadres van de lead
            name: Naam van de lead
            
        Returns:
            True als het verzoek succesvol is verstuurd
        """
        if not self.webhook_url:
            print("⚠️  CLAY_WEBHOOK_URL niet geconfigureerd. Stel in via .env")
            return False

        payload = {
            "lead_id": lead_id,
            "linkedin_url": linkedin_url,
            "email": email,
            "name": name,
        }

        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if resp.status_code in (200, 201, 202):
                print(f"✅ Clay enrichment gestart voor {linkedin_url}")
                return True
            else:
                print(f"⚠️  Clay enrichment fout: {resp.status_code} — {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Clay enrichment mislukt: {e}")
            return False

    @staticmethod
    def parse_clay_response(clay_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Clay enrichment response naar ons formaat.
        
        Clay kan verschillende velden teruggeven afhankelijk van 
        de enrichment provider (Apollo, PeopleDataLabs, etc.).
        Dit normaliseert de data naar ons schema.
        """
        return {
            "headline": (
                clay_data.get("linkedin_headline")
                or clay_data.get("headline")
                or clay_data.get("title")
                or ""
            ),
            "about": (
                clay_data.get("linkedin_summary")
                or clay_data.get("summary")
                or clay_data.get("bio")
                or ""
            ),
            "job_title": (
                clay_data.get("job_title")
                or clay_data.get("title")
                or clay_data.get("current_title")
                or ""
            ),
            "employer": (
                clay_data.get("company_name")
                or clay_data.get("organization_name")
                or clay_data.get("company")
                or ""
            ),
            "location": (
                clay_data.get("location")
                or clay_data.get("city")
                or ""
            ),
            "profile_photo_url": (
                clay_data.get("photo_url")
                or clay_data.get("linkedin_photo_url")
                or clay_data.get("profile_pic")
                or ""
            ),
            "experience": clay_data.get("experience", []),
            "skills": clay_data.get("skills", []),
            "education": clay_data.get("education", []),
        }


if __name__ == "__main__":
    print("Clay enrichment client")
    print("Stappen om te configureren:")
    print("1. Maak een Clay table aan op app.clay.com")
    print("2. Voeg een webhook trigger toe")
    print("3. Voeg 'Enrich Person from LinkedIn URL' actie toe")    
    print("4. Stel CLAY_WEBHOOK_URL in via .env")
    print("5. Stel een webhookback in naar /webhook/clay-callback")
