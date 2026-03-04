"""
SEO Analyzer
Analyseert het profiel op ontbrekende en aanbevolen SEO keywords.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProfileIntake, SEOKeyword


# ============================================================
# BRANCHE-SPECIFIEKE SEO KEYWORD DATABASE
# ============================================================

SEO_DATABASE = {
    "Bouw & Infra": {
        "critical": [
            ("Toezichthouder", "Primaire functietitel die recruiters zoeken", "headline"),
            ("Bouwregelgeving", "Essentieel voor bouw/overheid functies", "skills"),
            ("Omgevingswet", "Wettelijk kader dat kennis van regelgeving benadrukt", "about"),
            ("Vergunningsverlening", "Kerncompetentie in bouw toezicht", "skills"),
            ("Handhaving", "Toont autoriteit en ervaring met naleving", "about"),
        ],
        "recommended": [
            ("Ruimtelijke Ordening", "Vergroot vindbaarheid binnen overheid", "headline"),
            ("VCA", "Veiligheidscertificaat, toont compliance", "skills"),
            ("BIM", "Building Information Modeling — moderne bouwkennis", "skills"),
            ("AutoCAD", "Technische tekenvaardigheid", "skills"),
            ("Omgevingsdienst", "Directe match met werkomgeving", "about"),
            ("Projectleider", "Leiderschap in bouwprojecten", "experience"),
            ("Kwaliteitscontrole", "Toont oog voor kwaliteit", "experience"),
            ("Inspectie", "Kerntaak van toezichthouders", "about"),
            ("Bouwbesluit", "Wettelijke kennis", "skills"),
            ("Duurzaam bouwen", "Toekomstgerichte expertise", "skills"),
        ]
    },
    "Techniek & Industrie": {
        "critical": [
            ("Engineer", "Basis zoekterm voor technische rollen", "headline"),
            ("Technisch", "Onderscheidt van generieke functies", "headline"),
            ("Productie", "Kernomgeving voor industriële functies", "about"),
            ("Automatisering", "Toont moderne technische kennis", "skills"),
            ("Onderhoud", "Maintenance is schaarse expertise", "skills"),
        ],
        "recommended": [
            ("PLC", "Specifieke technische vaardigheid", "skills"),
            ("Lean Manufacturing", "Procesoptimalisatie methodiek", "skills"),
            ("Werkvoorbereider", "Veelgevraagde functie", "headline"),
            ("Kwaliteitsmanagement", "Toont systematische aanpak", "experience"),
            ("R&D", "Research & Development", "about"),
            ("Six Sigma", "Kwaliteitsmethodiek", "skills"),
            ("MES", "Manufacturing Execution System", "skills"),
            ("SCADA", "Supervisory Control kennis", "skills"),
            ("Procesoptimalisatie", "Efficiëntie verbetering", "experience"),
            ("Elektrotechniek", "Technische specialisatie", "skills"),
        ]
    },
    "IT & Software": {
        "critical": [
            ("Software Developer", "Primaire zoekterm", "headline"),
            ("Full-Stack", "Toont brede technische kennis", "headline"),
            ("Agile", "Methodiek die vrijwel overal vereist is", "skills"),
            ("Cloud", "AWS/Azure/GCP — moderne infrastructuur", "skills"),
            ("DevOps", "Deployment en operations", "skills"),
        ],
        "recommended": [
            ("Python", "Populairste programmeertaal", "skills"),
            ("JavaScript", "Frontend/backend taal", "skills"),
            ("React", "Populairste frontend framework", "skills"),
            ("Kubernetes", "Container orchestration", "skills"),
            ("CI/CD", "Continuous Integration/Deployment", "skills"),
            ("Microservices", "Moderne architectuur", "experience"),
            ("Data Engineering", "Groeiend specialisme", "about"),
            ("Machine Learning", "AI/ML expertise", "skills"),
            ("Security", "Cybersecurity awareness", "skills"),
            ("Scrum Master", "Agile rol certificering", "skills"),
        ]
    },
    "Overheid & Publieke Sector": {
        "critical": [
            ("Toezichthouder", "Kerntitel overheid", "headline"),
            ("Beleid", "Beleidsvorming en -uitvoering", "about"),
            ("Handhaving", "Kern overheidstaak", "skills"),
            ("Omgevingswet", "Actuele wetgeving", "skills"),
            ("Adviseur", "Adviseursrol binnen overheid", "headline"),
        ],
        "recommended": [
            ("Gemeente", "Werkcontext", "about"),
            ("Provincie", "Werkcontext", "about"),
            ("Juridisch", "Wettelijke achtergrond", "skills"),
            ("WOO", "Wet open overheid", "skills"),
            ("Regelgeving", "Kennis van regels en wetten", "about"),
            ("Participatie", "Burgerparticipatie", "skills"),
            ("Bestemmingsplan", "Ruimtelijke planning", "skills"),
            ("Subsidie", "Subsidiebeheer", "skills"),
            ("Digitalisering", "Moderne overheid", "about"),
            ("Samenwerking", "Interdisciplinair werk", "skills"),
        ]
    },
    "Engineering & R&D": {
        "critical": [
            ("Engineer", "Basis zoekterm", "headline"),
            ("Ontwerp", "Design engineering", "about"),
            ("R&D", "Research & Development", "headline"),
            ("Innovatie", "Vernieuwingsgerichtheid", "about"),
            ("CAD", "Computer-Aided Design", "skills"),
        ],
        "recommended": [
            ("Prototype", "Productontwikkeling", "experience"),
            ("Validatie", "Test en validatie", "skills"),
            ("Simulatie", "FEA/CFD simulaties", "skills"),
            ("Mechatronica", "Multi-disciplinair", "skills"),
            ("Embedded", "Embedded systems", "skills"),
            ("Materiaal", "Materiaalkunde", "skills"),
            ("3D Printing", "Additive manufacturing", "skills"),
            ("Patent", "Intellectueel eigendom", "experience"),
            ("Testen", "Testmethodologie", "skills"),
            ("Systems Engineering", "Systeem denken", "skills"),
        ]
    },
    "HR & Recruitment": {
        "critical": [
            ("Recruitment", "Primaire zoekterm", "headline"),
            ("Talent Acquisition", "Internationale terminologie", "headline"),
            ("Sourcing", "Actief werven", "skills"),
            ("Employer Branding", "Werkgeversmerk", "about"),
            ("HR", "Human Resources", "headline"),
        ],
        "recommended": [
            ("RPO", "Recruitment Process Outsourcing", "about"),
            ("Arbeidsmarkt", "Marktkennis", "about"),
            ("Assessment", "Beoordeling kandidaten", "skills"),
            ("Onboarding", "Inwerkproces", "skills"),
            ("ATS", "Applicant Tracking System", "skills"),
            ("Data-driven", "Analytische aanpak", "about"),
            ("Werving & Selectie", "Nederlandse terminologie", "skills"),
            ("Detachering", "Uitzendmodel", "about"),
            ("Interim", "Tijdelijke oplossingen", "about"),
            ("LinkedIn Recruiter", "Tool expertise", "skills"),
        ]
    },
}


def analyze_seo(intake: ProfileIntake) -> list[SEOKeyword]:
    """
    Analyseert het profiel op ontbrekende SEO keywords
    en geeft aanbevelingen per keyword.
    """
    # Verzamel alle profieltekst
    full_text = " ".join([
        intake.current_headline or "",
        intake.current_about or "",
        intake.current_job_title or "",
        intake.current_job_description or "",
        intake.current_skills or "",
        intake.education or "",
        intake.certificates or "",
        intake.unique_value or "",
        intake.top_3_skills or "",
    ]).lower()

    # Zoek de juiste sector database
    sector_data = _get_sector_data(intake.target_sector)
    if not sector_data:
        # Fallback: gebruik alle sectoren
        sector_data = {"critical": [], "recommended": []}
        for data in SEO_DATABASE.values():
            sector_data["critical"].extend(data["critical"])
            sector_data["recommended"].extend(data["recommended"])

    results = []

    # Check critical keywords (hogere relevantie)
    for keyword, reason, where in sector_data["critical"]:
        found = keyword.lower() in full_text
        if not found:
            results.append(SEOKeyword(
                keyword=keyword,
                relevance_score=10,
                reason=f"🔴 KRITIEK — {reason}",
                where_to_add=where
            ))

    # Check recommended keywords
    for keyword, reason, where in sector_data["recommended"]:
        found = keyword.lower() in full_text
        if not found:
            results.append(SEOKeyword(
                keyword=keyword,
                relevance_score=7,
                reason=f"🟡 AANBEVOLEN — {reason}",
                where_to_add=where
            ))

    # Sorteer op relevantie (hoogste eerst) en limit tot top 10
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results[:10]


def get_keyword_coverage(intake: ProfileIntake) -> dict:
    """
    Berekent het percentage keyword coverage per sectie van het profiel.
    """
    sector_data = _get_sector_data(intake.target_sector)
    if not sector_data:
        return {"total_coverage": 0, "sections": {}}

    all_keywords = [kw for kw, _, _ in sector_data["critical"]] + \
                   [kw for kw, _, _ in sector_data["recommended"]]

    sections = {
        "headline": (intake.current_headline or "").lower(),
        "about": (intake.current_about or "").lower(),
        "experience": (intake.current_job_description or "").lower(),
        "skills": (intake.current_skills or "").lower(),
    }

    coverage = {}
    total_found = 0
    total_keywords = len(all_keywords)

    for section_name, section_text in sections.items():
        found = [kw for kw in all_keywords if kw.lower() in section_text]
        coverage[section_name] = {
            "found": found,
            "count": len(found),
            "percentage": round(len(found) / max(total_keywords, 1) * 100)
        }
        total_found += len(found)

    # Unieke keywords gevonden over alle secties
    full_text = " ".join(sections.values())
    unique_found = sum(1 for kw in all_keywords if kw.lower() in full_text)

    return {
        "total_coverage": round(unique_found / max(total_keywords, 1) * 100),
        "unique_found": unique_found,
        "total_keywords": total_keywords,
        "sections": coverage
    }


def _get_sector_data(sector: str) -> dict | None:
    """Zoekt de juiste sector database op."""
    for key, data in SEO_DATABASE.items():
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            return data
    return None


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Gebruik: python seo_analyzer.py <intake.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    test = ProfileIntake(**data)

    print("=" * 60)
    print("🔍 SEO KEYWORD ANALYSE")
    print("=" * 60)

    keywords = analyze_seo(test)
    for kw in keywords:
        print(f"\n  📌 {kw.keyword} (Relevantie: {kw.relevance_score}/10)")
        print(f"     {kw.reason}")
        print(f"     ➡️  Toevoegen aan: {kw.where_to_add}")

    print("\n" + "=" * 60)
    print("📊 KEYWORD COVERAGE")
    print("=" * 60)
    coverage = get_keyword_coverage(test)
    print(f"\n  Totale coverage: {coverage['total_coverage']}%")
    print(f"  Gevonden: {coverage['unique_found']}/{coverage['total_keywords']} keywords")
    for section, data in coverage["sections"].items():
        print(f"  {section:15s}: {data['count']} keywords ({data['percentage']}%)")
