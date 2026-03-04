"""
Pipedrive client — Maakt deals aan voor qualified leads.
Een lead is 'qualified' als de LinkedIn profiel score >= threshold.

Pipedrive API docs: https://developers.pipedrive.com/docs/api/v1

Flow:
    1. LinkedIn analyse → score berekend
    2. Score >= QUALIFIED_SCORE_THRESHOLD → deal aanmaken in Pipedrive
    3. Deal bevat: contact info, score, LinkedIn URL, rapport link
"""

import os
import requests
from typing import Optional, Dict, Any


class PipedriveClient:
    """Client voor Pipedrive CRM integratie."""

    def __init__(self):
        self.api_key = os.environ.get("PIPEDRIVE_API_KEY", "")
        self.domain = os.environ.get("PIPEDRIVE_DOMAIN", "recruitin")
        self.base_url = f"https://{self.domain}.pipedrive.com/api/v1"
        self.qualified_threshold = int(os.environ.get("QUALIFIED_SCORE_THRESHOLD", "50"))

        if not self.api_key:
            print("⚠️  PIPEDRIVE_API_KEY niet geconfigureerd in .env")

    def _params(self) -> dict:
        return {"api_token": self.api_key}

    def is_qualified(self, score: int) -> bool:
        """Check of een lead qualified is op basis van profiel score."""
        return score >= self.qualified_threshold

    def create_person(
        self,
        name: str,
        email: str,
        phone: str = "",
        linkedin_url: str = "",
    ) -> Optional[int]:
        """Maak een persoon aan in Pipedrive.

        Returns:
            Person ID of None bij fout
        """
        if not self.api_key:
            print("⚠️  PIPEDRIVE_API_KEY niet geconfigureerd")
            return None

        payload = {
            "name": name,
            "email": [{"value": email, "primary": True, "label": "work"}],
        }

        if phone:
            payload["phone"] = [{"value": phone, "primary": True, "label": "work"}]

        # LinkedIn URL als custom veld (als je dat hebt ingesteld in Pipedrive)
        # payload["<custom_field_key>"] = linkedin_url

        try:
            resp = requests.post(
                f"{self.base_url}/persons",
                json=payload,
                params=self._params(),
                timeout=10,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                if data.get("success"):
                    person_id = data["data"]["id"]
                    print(f"✅ Pipedrive persoon aangemaakt: {name} (ID: {person_id})")
                    return person_id

            # Check of persoon al bestaat
            resp_search = requests.get(
                f"{self.base_url}/persons/search",
                params={**self._params(), "term": email, "fields": "email"},
                timeout=10,
            )
            if resp_search.status_code == 200:
                results = resp_search.json().get("data", {}).get("items", [])
                if results:
                    person_id = results[0]["item"]["id"]
                    print(f"ℹ️  Pipedrive persoon bestaat al: {name} (ID: {person_id})")
                    return person_id

            print(f"⚠️  Pipedrive persoon fout: {resp.status_code} — {resp.text}")
            return None

        except Exception as e:
            print(f"❌ Pipedrive persoon fout: {e}")
            return None

    def create_deal(
        self,
        title: str,
        person_id: int,
        score: int = 0,
        grade: str = "",
        linkedin_url: str = "",
        note: str = "",
    ) -> Optional[int]:
        """Maak een deal aan in Pipedrive.

        Args:
            title: Deal titel (bijv. "LinkedIn Optimizer — Jan de Vries")
            person_id: Pipedrive person ID
            score: Profiel score
            grade: Profiel grade
            linkedin_url: LinkedIn URL
            note: Extra notitie

        Returns:
            Deal ID of None bij fout
        """
        if not self.api_key:
            return None

        payload = {
            "title": title,
            "person_id": person_id,
            "status": "open",
            # Stel een pipeline/stage in als je dat hebt geconfigureerd
            # "pipeline_id": 1,
            # "stage_id": 1,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/deals",
                json=payload,
                params=self._params(),
                timeout=10,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                if data.get("success"):
                    deal_id = data["data"]["id"]
                    print(f"✅ Pipedrive deal aangemaakt: {title} (ID: {deal_id})")

                    # Voeg notitie toe met score details
                    if note or score:
                        note_text = note or (
                            f"LinkedIn Profiel Analyse\n"
                            f"Score: {score}/100 (Grade {grade})\n"
                            f"LinkedIn: {linkedin_url}\n"
                            f"Qualified: Ja (score >= {self.qualified_threshold})"
                        )
                        self._add_note(deal_id, note_text)

                    return deal_id

            print(f"⚠️  Pipedrive deal fout: {resp.status_code} — {resp.text}")
            return None

        except Exception as e:
            print(f"❌ Pipedrive deal fout: {e}")
            return None

    def _add_note(self, deal_id: int, content: str):
        """Voeg een notitie toe aan een deal."""
        try:
            requests.post(
                f"{self.base_url}/notes",
                json={
                    "deal_id": deal_id,
                    "content": content,
                    "pinned_to_deal_flag": 1,
                },
                params=self._params(),
                timeout=10,
            )
        except Exception:
            pass  # Notitie is niet kritiek

    def create_qualified_lead(
        self,
        name: str,
        email: str,
        phone: str = "",
        linkedin_url: str = "",
        score: int = 0,
        grade: str = "",
    ) -> Optional[int]:
        """Convenience: maak persoon + deal aan voor een qualified lead.

        Returns:
            Deal ID of None
        """
        if not self.is_qualified(score):
            print(f"ℹ️  Lead {name} niet qualified (score {score} < {self.qualified_threshold})")
            return None

        print(f"\n🏆 Qualified lead: {name} (score: {score}, grade: {grade})")

        person_id = self.create_person(name, email, phone, linkedin_url)
        if not person_id:
            return None

        deal_id = self.create_deal(
            title=f"LinkedIn Optimizer — {name}",
            person_id=person_id,
            score=score,
            grade=grade,
            linkedin_url=linkedin_url,
        )

        return deal_id


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    client = PipedriveClient()
    print(f"Pipedrive client")
    print(f"  Domain: {client.domain}")
    print(f"  API key: {'✅ ingesteld' if client.api_key else '❌ ontbreekt'}")
    print(f"  Qualified threshold: {client.qualified_threshold}")
