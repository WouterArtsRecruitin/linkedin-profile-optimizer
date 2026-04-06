"""
LinkedIn Profile Scraper
Haalt publiek beschikbare data op van een LinkedIn profiel.

Strategie (in volgorde):
1. Proxycurl API (als PROXYCURL_API_KEY geconfigureerd)
2. Publiek profiel HTML scraping (meta tags + JSON-LD)
3. Fallback: lege dict (caller gebruikt defaults)
"""

import os
import re
import json
from typing import Dict, Optional

import httpx


def scrape_linkedin_profile(linkedin_url: str) -> Dict[str, str]:
    """
    Probeert LinkedIn profiel data op te halen.
    Returns dict met beschikbare velden:
        headline, about, location, job_title, employer, profile_photo_url
    Lege dict als niets gevonden.
    """
    # Normaliseer URL
    linkedin_url = _normalize_url(linkedin_url)
    if not linkedin_url:
        print("   ⚠️ Ongeldige LinkedIn URL")
        return {}

    # Strategie 1: Proxycurl API
    proxycurl_key = os.environ.get("PROXYCURL_API_KEY", "")
    if proxycurl_key:
        print("   🔍 LinkedIn scraping via Proxycurl...")
        result = _scrape_via_proxycurl(linkedin_url, proxycurl_key)
        if result:
            return result

    # Strategie 2: Publiek profiel HTML
    print("   🔍 LinkedIn scraping via publiek profiel...")
    result = _scrape_public_profile(linkedin_url)
    if result:
        return result

    print("   ⚠️ Geen LinkedIn data gevonden — defaults worden gebruikt")
    return {}


def _normalize_url(url: str) -> str:
    """Normaliseer LinkedIn URL naar https://www.linkedin.com/in/username format."""
    if not url:
        return ""
    url = url.strip()
    # Extract username from various URL formats
    match = re.search(r'linkedin\.com/(?:in|pub)/([a-zA-Z0-9\-_%.]+)', url)
    if match:
        username = match.group(1).rstrip('/')
        return f"https://www.linkedin.com/in/{username}"
    return ""


def _scrape_via_proxycurl(linkedin_url: str, api_key: str) -> Optional[Dict[str, str]]:
    """
    Proxycurl API — betrouwbare LinkedIn scraping ($0.01/credit).
    Docs: https://nubela.co/proxycurl/docs
    """
    try:
        response = httpx.get(
            "https://nubela.co/proxycurl/api/v2/linkedin",
            params={
                "url": linkedin_url,
                "use_cache": "if-recent",
                "fallback_to_cache": "on-error",
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            result = {
                "headline": data.get("headline", ""),
                "about": data.get("summary", ""),
                "location": _format_location(data),
                "job_title": "",
                "employer": "",
                "profile_photo_url": data.get("profile_pic_url", ""),
            }

            # Huidige functie uit experiences
            experiences = data.get("experiences", [])
            if experiences:
                current = experiences[0]  # Meest recente
                result["job_title"] = current.get("title", "")
                result["employer"] = current.get("company", "")

            # Filter lege waarden
            result = {k: v for k, v in result.items() if v}
            if result:
                print(f"   ✅ Proxycurl: {len(result)} velden gevonden")
            return result if result else None

        elif response.status_code == 404:
            print(f"   ⚠️ Proxycurl: profiel niet gevonden")
        elif response.status_code == 429:
            print(f"   ⚠️ Proxycurl: rate limit bereikt")
        elif response.status_code == 403:
            print(f"   ⚠️ Proxycurl: ongeldige API key")
        else:
            print(f"   ⚠️ Proxycurl: HTTP {response.status_code}")

        return None

    except Exception as e:
        print(f"   ⚠️ Proxycurl fout: {e}")
        return None


def _scrape_public_profile(linkedin_url: str) -> Optional[Dict[str, str]]:
    """
    Scrape publiek LinkedIn profiel via HTML meta tags.
    LinkedIn geeft beperkte data aan niet-ingelogde gebruikers,
    maar meta tags (og:title, og:description) bevatten vaak headline + samenvatting.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        }

        response = httpx.get(linkedin_url, headers=headers, timeout=15.0, follow_redirects=True)

        if response.status_code != 200:
            print(f"   ⚠️ LinkedIn HTTP {response.status_code}")
            return None

        html = response.text
        result = {}

        # og:title bevat vaak "Naam - Headline - LinkedIn"
        og_title = _extract_meta(html, "og:title")
        if og_title:
            parts = og_title.split(" - ")
            if len(parts) >= 2:
                # Eerste deel = naam (al bekend), tweede = headline
                headline = parts[1].strip() if parts[1].strip() != "LinkedIn" else ""
                if headline:
                    result["headline"] = headline

        # og:description bevat vaak een samenvatting
        og_desc = _extract_meta(html, "og:description")
        if og_desc and len(og_desc) > 30:
            # Filter "View X's profile on LinkedIn" tekst
            if "profile on LinkedIn" not in og_desc and "professional profile" not in og_desc:
                result["about"] = og_desc[:500]  # Eerste 500 chars

        # og:image = profielfoto
        og_image = _extract_meta(html, "og:image")
        if og_image and "linkedin.com" in og_image and "shrink_100_100" not in og_image:
            result["profile_photo_url"] = og_image

        # Probeer locatie uit description
        geo_region = _extract_meta(html, "geo.region")
        if geo_region:
            result["location"] = geo_region

        # JSON-LD structured data (als beschikbaar)
        jsonld = _extract_jsonld(html)
        if jsonld:
            if jsonld.get("jobTitle") and "job_title" not in result:
                result["job_title"] = jsonld["jobTitle"]
            if jsonld.get("worksFor") and "employer" not in result:
                employer = jsonld["worksFor"]
                if isinstance(employer, dict):
                    result["employer"] = employer.get("name", "")
                elif isinstance(employer, str):
                    result["employer"] = employer
            if jsonld.get("address") and "location" not in result:
                addr = jsonld["address"]
                if isinstance(addr, dict):
                    result["location"] = addr.get("addressLocality", "")

        # Filter lege waarden
        result = {k: v for k, v in result.items() if v}
        if result:
            print(f"   ✅ Publiek profiel: {len(result)} velden gevonden ({', '.join(result.keys())})")
        return result if result else None

    except Exception as e:
        print(f"   ⚠️ Public profile scraping fout: {e}")
        return None


def _extract_meta(html: str, property_name: str) -> str:
    """Extract content van een meta tag."""
    # property= variant (Open Graph)
    match = re.search(
        rf'<meta\s+(?:property|name)=["\'](?:og:)?{re.escape(property_name)}["\']\s+content=["\']([^"\']*)["\']',
        html, re.IGNORECASE
    )
    if not match:
        # content= eerst variant
        match = re.search(
            rf'<meta\s+content=["\']([^"\']*?)["\']\s+(?:property|name)=["\'](?:og:)?{re.escape(property_name)}["\']',
            html, re.IGNORECASE
        )
    return match.group(1).strip() if match else ""


def _extract_jsonld(html: str) -> Optional[Dict]:
    """Probeer JSON-LD Person data te vinden."""
    try:
        pattern = r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        for match in matches:
            data = json.loads(match.strip())
            if isinstance(data, dict) and data.get("@type") == "Person":
                return data
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Person":
                        return item
    except (json.JSONDecodeError, Exception):
        pass
    return None


def _format_location(data: Dict) -> str:
    """Format locatie uit Proxycurl data."""
    city = data.get("city", "")
    state = data.get("state", "")
    country = data.get("country_full_name", "")
    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts)
