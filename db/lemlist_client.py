"""
Lemlist client — Voegt leads toe aan Lemlist campaigns.
Gebruikt voor het versturen van LinkedIn analyse rapporten.

Lemlist API docs: https://developer.lemlist.com/

Flow:
    1. Lead genereert rapport via LinkedIn Optimizer
    2. Lead wordt toegevoegd aan Lemlist campaign met rapport als variabele
    3. Lemlist stuurt gepersonaliseerde email met rapport link/bijlage
"""

import os
import requests
from typing import Optional, Dict, Any


class LemlistClient:
    """Client voor Lemlist email campaign integratie."""

    def __init__(self):
        self.api_key = os.environ.get("LEMLIST_API_KEY", "")
        self.team_id = os.environ.get("LEMLIST_TEAM_ID", "tea_YdDiwvc4qhMXF3MmZ")
        self.campaign_id = os.environ.get("LEMLIST_CAMPAIGN_ID", "")
        self.base_url = "https://api.lemlist.com/api"

        if not self.api_key:
            print("⚠️  LEMLIST_API_KEY niet geconfigureerd in .env")

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
        }

    def _auth(self) -> tuple:
        """Lemlist gebruikt Basic Auth met lege username en API key als password."""
        return ("", self.api_key)

    def add_lead_to_campaign(
        self,
        campaign_id: str,
        email: str,
        first_name: str,
        last_name: str = "",
        linkedin_url: str = "",
        score: int = 0,
        grade: str = "",
        report_url: str = "",
        banner_url: str = "",
        extra_variables: Dict[str, Any] = None,
    ) -> bool:
        """Voeg een lead toe aan een Lemlist campaign.

        De variabelen (score, grade, report_url, etc.) worden beschikbaar
        als {{score}}, {{grade}}, {{reportUrl}} in de Lemlist email templates.

        Args:
            campaign_id: Lemlist campaign ID
            email: Lead email
            first_name: Voornaam
            last_name: Achternaam
            linkedin_url: LinkedIn profiel URL
            score: Profiel score (0-100)
            grade: Profiel grade (A-F)
            report_url: URL naar het rapport (hosted)
            banner_url: URL naar de banner (hosted)
            extra_variables: Extra template variabelen

        Returns:
            True als de lead succesvol is toegevoegd
        """
        if not self.api_key:
            print("⚠️  LEMLIST_API_KEY niet geconfigureerd")
            return False

        cid = campaign_id or self.campaign_id
        if not cid:
            print("⚠️  Geen campaign_id opgegeven of LEMLIST_CAMPAIGN_ID niet ingesteld")
            return False

        url = f"{self.base_url}/campaigns/{cid}/leads/{email}"

        payload = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "linkedinUrl": linkedin_url,
            "companyName": "",
            # Custom variabelen beschikbaar in Lemlist templates
            "score": str(score),
            "grade": grade,
            "reportUrl": report_url,
            "bannerUrl": banner_url,
        }

        if extra_variables:
            payload.update(extra_variables)

        try:
            resp = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                auth=self._auth(),
                timeout=10,
            )

            if resp.status_code in (200, 201):
                print(f"✅ Lead {email} toegevoegd aan Lemlist campaign {cid}")
                return True
            elif resp.status_code == 409:
                print(f"ℹ️  Lead {email} zit al in campaign {cid}")
                return True  # Al toegevoegd is ook ok
            else:
                print(f"⚠️  Lemlist fout: {resp.status_code} — {resp.text}")
                return False

        except Exception as e:
            print(f"❌ Lemlist fout: {e}")
            return False

    def get_campaigns(self) -> list:
        """Haal alle campaigns op (handig voor het vinden van campaign IDs)."""
        if not self.api_key:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/campaigns",
                auth=self._auth(),
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    client = LemlistClient()

    if client.api_key:
        print("📋 Lemlist campaigns ophalen...")
        campaigns = client.get_campaigns()
        for c in campaigns:
            print(f"   • {c.get('_id')}: {c.get('name')}")
        if not campaigns:
            print("   Geen campaigns gevonden (of API key onjuist)")
    else:
        print("⚠️  Stel LEMLIST_API_KEY in via .env")
        print("   Te vinden in: Lemlist → Settings → Integrations → API")
