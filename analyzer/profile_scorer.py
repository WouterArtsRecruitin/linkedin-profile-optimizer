"""
LinkedIn Profile Scorer
Scoort een LinkedIn profiel op 10 criteria met een totaalscore van 0-100.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProfileIntake, ProfileScore, ScoreCategory


# ============================================================
# SECTOR-SPECIFIEKE KEYWORDS DATABASE
# ============================================================

SECTOR_KEYWORDS = {
    "Bouw & Infra": [
        "toezichthouder", "bouwregelgeving", "omgevingswet", "vergunning",
        "handhaving", "projectleider", "infra", "civiel", "bouwplaats",
        "veiligheid", "VCA", "werkvoorbereider", "constructeur", "BIM"
    ],
    "Techniek & Industrie": [
        "engineer", "technisch", "productie", "automatisering", "PLC",
        "onderhoud", "maintenance", "werktuigbouw", "elektrotechniek",
        "procesoptimalisatie", "lean", "kwaliteit", "R&D"
    ],
    "IT & Software": [
        "developer", "software", "cloud", "devops", "agile", "scrum",
        "full-stack", "python", "javascript", "architectuur", "data",
        "AI", "machine learning", "security"
    ],
    "Overheid & Publieke Sector": [
        "toezichthouder", "handhaving", "beleid", "vergunning",
        "omgevingswet", "ruimtelijke ordening", "gemeente", "provincie",
        "adviseur", "regelgeving", "juridisch", "WOO"
    ],
    "Engineering & R&D": [
        "engineer", "ontwerp", "R&D", "innovatie", "prototype",
        "testen", "validatie", "CAD", "simulatie", "materiaal",
        "mechatronica", "embedded", "firmware"
    ],
    "HR & Recruitment": [
        "recruitment", "sourcing", "talent", "werving", "selectie",
        "employer branding", "HR", "arbeidsmarkt", "assessment",
        "onboarding", "RPO", "detachering"
    ],
}

# Standaard keywords als sector niet gevonden wordt
DEFAULT_KEYWORDS = [
    "leiderschap", "management", "strategie", "resultaatgericht",
    "samenwerking", "communicatie", "project", "analyse", "planning"
]


def score_profile(intake: ProfileIntake) -> ProfileScore:
    """
    Berekent de totale profielscore op basis van 10 categorieën.
    Elke categorie scoort 0-10, gewogen naar het belang.
    """
    categories = []

    # 1. HEADLINE (15%)
    headline_score, headline_feedback, headline_suggestions = _score_headline(intake)
    categories.append(ScoreCategory(
        name="Headline / Kopregel",
        score=headline_score,
        weight_pct=15,
        feedback=headline_feedback,
        suggestions=headline_suggestions
    ))

    # 2. OVER MIJ (15%)
    about_score, about_feedback, about_suggestions = _score_about(intake)
    categories.append(ScoreCategory(
        name="Over Mij / About",
        score=about_score,
        weight_pct=15,
        feedback=about_feedback,
        suggestions=about_suggestions
    ))

    # 3. WERKERVARING (15%)
    exp_score, exp_feedback, exp_suggestions = _score_experience(intake)
    categories.append(ScoreCategory(
        name="Werkervaring",
        score=exp_score,
        weight_pct=15,
        feedback=exp_feedback,
        suggestions=exp_suggestions
    ))

    # 4. VAARDIGHEDEN (10%)
    skills_score, skills_feedback, skills_suggestions = _score_skills(intake)
    categories.append(ScoreCategory(
        name="Vaardigheden / Skills",
        score=skills_score,
        weight_pct=10,
        feedback=skills_feedback,
        suggestions=skills_suggestions
    ))

    # 5. PROFIELFOTO (5%)
    photo_score, photo_feedback, photo_suggestions = _score_photo(intake)
    categories.append(ScoreCategory(
        name="Profielfoto",
        score=photo_score,
        weight_pct=5,
        feedback=photo_feedback,
        suggestions=photo_suggestions
    ))

    # 6. BANNER (5%)
    banner_score, banner_feedback, banner_suggestions = _score_banner(intake)
    categories.append(ScoreCategory(
        name="Banner",
        score=banner_score,
        weight_pct=5,
        feedback=banner_feedback,
        suggestions=banner_suggestions
    ))

    # 7. SEO KEYWORDS (15%)
    seo_score, seo_feedback, seo_suggestions = _score_seo(intake)
    categories.append(ScoreCategory(
        name="SEO & Keywords",
        score=seo_score,
        weight_pct=15,
        feedback=seo_feedback,
        suggestions=seo_suggestions
    ))

    # 8. OPLEIDING (5%)
    edu_score, edu_feedback, edu_suggestions = _score_education(intake)
    categories.append(ScoreCategory(
        name="Opleiding & Certificaten",
        score=edu_score,
        weight_pct=5,
        feedback=edu_feedback,
        suggestions=edu_suggestions
    ))

    # 9. ONDERSCHEIDEND VERMOGEN (10%)
    uv_score, uv_feedback, uv_suggestions = _score_unique_value(intake)
    categories.append(ScoreCategory(
        name="Onderscheidend Vermogen",
        score=uv_score,
        weight_pct=10,
        feedback=uv_feedback,
        suggestions=uv_suggestions
    ))

    # 10. DOELGROEP AANSLUITING (5%)
    audience_score, audience_feedback, audience_suggestions = _score_audience_fit(intake)
    categories.append(ScoreCategory(
        name="Doelgroep Aansluiting",
        score=audience_score,
        weight_pct=5,
        feedback=audience_feedback,
        suggestions=audience_suggestions
    ))

    # Bereken totaal (gewogen gemiddelde)
    total = 0
    for cat in categories:
        total += (cat.score / cat.max_score) * cat.weight_pct
    total = round(total)

    # Pak de top verbeterpunten
    sorted_cats = sorted(categories, key=lambda c: c.score)
    top_improvements = []
    for cat in sorted_cats[:3]:
        if cat.suggestions:
            top_improvements.append(f"{cat.name}: {cat.suggestions[0]}")

    profile_score = ProfileScore(
        total_score=total,
        categories=categories,
        summary=_generate_summary(total, intake),
        top_improvements=top_improvements
    )
    profile_score.grade = profile_score.calculate_grade()

    return profile_score


# ============================================================
# INDIVIDUELE SCORING FUNCTIES
# ============================================================

def _score_headline(intake: ProfileIntake) -> tuple:
    score = 0
    feedback = ""
    suggestions = []
    headline = intake.current_headline.strip()

    if not headline:
        return 0, "Geen headline ingevuld.", ["Voeg een krachtige headline toe met je functie + waardepropositie"]

    # Lengte check (ideaal 60-120 tekens)
    if len(headline) >= 60:
        score += 3
    elif len(headline) >= 30:
        score += 2
    else:
        score += 1
        suggestions.append("Maak je headline langer (min. 60 tekens) — gebruik de ruimte voor keywords")

    # Bevat functietitel?
    if intake.current_job_title.lower() in headline.lower():
        score += 2
    else:
        suggestions.append(f"Voeg je functietitel '{intake.current_job_title}' toe aan je headline")

    # Bevat seperator (| of •)?
    if "|" in headline or "•" in headline or "–" in headline:
        score += 1
    else:
        suggestions.append("Gebruik separators (|) om secties te scheiden: 'Functie | Specialisme | Regio'")

    # Bevat sector/branche keywords?
    sector_kws = _get_sector_keywords(intake.target_sector)
    kw_found = sum(1 for kw in sector_kws if kw.lower() in headline.lower())
    if kw_found >= 2:
        score += 2
    elif kw_found >= 1:
        score += 1
    else:
        suggestions.append(f"Voeg relevante keywords toe: {', '.join(sector_kws[:3])}")

    # Bevat waardepropositie?
    value_indicators = ["help", "specialist", "expert", "ervaring", "jaar", "resultaat"]
    if any(v in headline.lower() for v in value_indicators):
        score += 2
    else:
        suggestions.append("Voeg ervaring of waardepropositie toe, bijv. '22j ervaring' of 'specialist in...'")

    score = min(score, 10)
    feedback = f"Score {score}/10 — Headline heeft {len(headline)} tekens, {kw_found} sector keywords gevonden."

    return score, feedback, suggestions


def _score_about(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []
    about = intake.current_about.strip()

    if not about or about.lower() == "geen":
        return 0, "Geen 'Over mij' tekst — dit is het belangrijkste onderdeel!", [
            "Schrijf een 'Over mij' van min. 150 woorden met het StoryBrand framework"
        ]

    word_count = len(about.split())

    # Lengte (ideaal 150-300 woorden)
    if word_count >= 150:
        score += 3
    elif word_count >= 80:
        score += 2
    elif word_count >= 30:
        score += 1
    else:
        suggestions.append(f"Je 'Over mij' is te kort ({word_count} woorden). Streef naar min. 150 woorden.")

    # Structuur (koppen, bulletpoints)
    has_structure = any(c in about for c in ["•", "✅", "1.", "2.", "3.", "→", "**", "STAP"])
    if has_structure:
        score += 2
    else:
        suggestions.append("Gebruik bulletpoints of genummerde stappen voor leesbaarheid")

    # CTA aanwezig?
    cta_words = ["stuur", "mail", "bel", "DM", "contact", "bericht", "kennismaking", "afspraak"]
    if any(c in about.lower() for c in cta_words):
        score += 2
    else:
        suggestions.append("Voeg een call-to-action toe: 'Stuur me een DM' of 'Mail me op...'")

    # SEO keywords in about?
    sector_kws = _get_sector_keywords(intake.target_sector)
    kw_in_about = sum(1 for kw in sector_kws if kw.lower() in about.lower())
    if kw_in_about >= 3:
        score += 2
    elif kw_in_about >= 1:
        score += 1
    else:
        suggestions.append(f"Verwerk deze keywords in je tekst: {', '.join(sector_kws[:5])}")

    # Persoonlijk (ik/mijn/wij)
    if any(w in about.lower() for w in [" ik ", " mijn ", " wij ", " ons "]):
        score += 1

    score = min(score, 10)
    feedback = f"Score {score}/10 — {word_count} woorden, {kw_in_about} keywords gevonden."

    return score, feedback, suggestions


def _score_experience(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []
    desc = intake.current_job_description.strip()

    if not desc:
        return 1, "Geen werkervaring beschrijving ingevuld.", [
            "Beschrijf je taken en resultaten met concrete getallen"
        ]

    word_count = len(desc.split())

    # Lengte
    if word_count >= 100:
        score += 3
    elif word_count >= 50:
        score += 2
    else:
        score += 1
        suggestions.append("Uitgebreidere werkervaring beschrijving (min. 100 woorden)")

    # Bevat getallen/metrics?
    import re
    numbers = re.findall(r'\d+', desc)
    if len(numbers) >= 3:
        score += 3
    elif len(numbers) >= 1:
        score += 2
    else:
        suggestions.append("Voeg concrete getallen toe: '50+ projecten', '95% tevredenheid', '€2M omzet'")

    # Bevat resultaten?
    result_words = ["resultaat", "bereikt", "gerealiseerd", "verbeterd", "opgeleverd", "✅", "succesvol"]
    if any(r in desc.lower() for r in result_words):
        score += 2
    else:
        suggestions.append("Toon resultaten: 'Resultaat: 95% klanttevredenheid bereikt'")

    # Heeft structuur?
    if any(c in desc for c in ["•", "✅", "-", "1.", "KERNTAKEN", "RESULTAAT"]):
        score += 2
    else:
        suggestions.append("Structureer met KERNTAKEN en RESULTAAT secties")

    score = min(score, 10)
    feedback = f"Score {score}/10 — {word_count} woorden beschrijving, {len(numbers)} getallen gebruikt."

    return score, feedback, suggestions


def _score_skills(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []
    skills = intake.parse_skills_list()

    if not skills:
        return 0, "Geen vaardigheden ingevuld.", [
            "Voeg minimaal 10 relevante vaardigheden toe"
        ]

    # Aantal (ideaal 10+)
    if len(skills) >= 10:
        score += 4
    elif len(skills) >= 6:
        score += 3
    elif len(skills) >= 3:
        score += 2
    else:
        score += 1
        suggestions.append(f"Je hebt {len(skills)} skills. Voeg er minstens {10 - len(skills)} toe.")

    # Sector-relevantie
    sector_kws = _get_sector_keywords(intake.target_sector)
    relevant = sum(1 for s in skills if any(kw.lower() in s.lower() for kw in sector_kws))
    if relevant >= 4:
        score += 3
    elif relevant >= 2:
        score += 2
    elif relevant >= 1:
        score += 1
    else:
        suggestions.append(f"Voeg sector-relevante skills toe: {', '.join(sector_kws[:5])}")

    # Variatie (niet alleen soft skills)
    hard_skill_indicators = ["AutoCAD", "Python", "PLC", "SAP", "Excel", "BIM", "Solidworks",
                             "toezicht", "handhaving", "vergunning", "engineering"]
    has_hard = any(any(h.lower() in s.lower() for h in hard_skill_indicators) for s in skills)
    if has_hard:
        score += 3
    else:
        score += 1
        suggestions.append("Voeg technische/hard skills toe naast soft skills")

    score = min(score, 10)
    feedback = f"Score {score}/10 — {len(skills)} vaardigheden, {relevant} sector-relevant."

    return score, feedback, suggestions


def _score_photo(intake: ProfileIntake) -> tuple:
    if intake.profile_photo_url:
        return 8, "Profielfoto aanwezig.", ["Controleer of de foto professioneel, scherp en goed uitgelicht is"]
    else:
        # PDF uploads bevatten geen foto-info — geef neutrale score, niet penaliseren
        return 5, "Profielfoto niet te beoordelen vanuit PDF.", [
            "Zorg voor een professionele foto: gezicht duidelijk zichtbaar, neutrale achtergrond"
        ]


def _score_banner(intake: ProfileIntake) -> tuple:
    if "Ja, en ik ben er tevreden" in intake.has_banner:
        return 8, "Je hebt een custom banner.", []
    elif "Ja, maar ik wil een betere" in intake.has_banner:
        return 5, "Je hebt een banner maar wilt verbetering.", [
            "We genereren een nieuwe, professionele banner op basis van je sector en branding"
        ]
    else:
        # PDF uploads bevatten geen banner-info — geef neutrale score
        return 5, "Banner niet te beoordelen vanuit PDF.", [
            "Een custom banner vergroot je professionele uitstraling — we maken er een voor je!"
        ]


def _score_seo(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []
    sector_kws = _get_sector_keywords(intake.target_sector)

    # Combineer alle tekstvelden
    full_text = " ".join([
        intake.current_headline,
        intake.current_about,
        intake.current_job_description,
        intake.current_skills,
        intake.current_job_title
    ]).lower()

    found_keywords = [kw for kw in sector_kws if kw.lower() in full_text]
    missing_keywords = [kw for kw in sector_kws if kw.lower() not in full_text]

    coverage = len(found_keywords) / max(len(sector_kws), 1)

    if coverage >= 0.6:
        score = 8
    elif coverage >= 0.4:
        score = 6
    elif coverage >= 0.2:
        score = 4
    else:
        score = 2

    if missing_keywords:
        suggestions.append(f"Ontbrekende keywords: {', '.join(missing_keywords[:5])}")

    feedback = f"Score {score}/10 — {len(found_keywords)}/{len(sector_kws)} sector keywords gevonden."

    return score, feedback, suggestions


def _score_education(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []
    edu_items = intake.parse_education_items()

    if not edu_items and not intake.education.strip():
        return 1, "Geen opleiding ingevuld.", ["Voeg je opleidingen toe, inclusief cursussen en certificaten"]

    if len(edu_items) >= 3:
        score += 4
    elif len(edu_items) >= 1:
        score += 2
    else:
        # Bare text aanwezig (niet geparsed)
        score += 2

    if intake.certificates and intake.certificates.strip():
        score += 3
    else:
        suggestions.append("Voeg relevante certificaten toe (VCA, PMP, Scrum, etc.)")

    # Bonus voor recente opleiding/certificaat
    if any(str(y) in intake.education for y in range(2020, 2027)):
        score += 3
    elif any(str(y) in intake.education for y in range(2015, 2020)):
        score += 2
    else:
        score += 1

    score = min(score, 10)
    feedback = f"Score {score}/10 — {len(edu_items)} opleidingen gevonden."

    return score, feedback, suggestions


def _score_unique_value(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []
    uv = intake.unique_value.strip()

    if not uv:
        return 1, "Geen onderscheidend vermogen ingevuld.", [
            "Benoem wat jou uniek maakt: combinatie van ervaring, specialisatie, of aanpak"
        ]

    word_count = len(uv.split())

    if word_count >= 30:
        score += 4
    elif word_count >= 15:
        score += 3
    else:
        score += 1
        suggestions.append("Beschrijf uitgebreider wat jou onderscheidt (min. 30 woorden)")

    # Bevat concrete differentiator?
    diff_words = ["combinatie", "uniek", "anders", "enige", "specialist", "ervaring", "jaar", "combineer"]
    if any(d in uv.lower() for d in diff_words):
        score += 3
    else:
        suggestions.append("Gebruik woorden als 'unieke combinatie van...' of 'specialist in...'")

    # Bevat getallen?
    import re
    if re.search(r'\d+', uv):
        score += 3
    else:
        suggestions.append("Onderbouw met getallen: '22 jaar ervaring', '500+ projecten'")

    score = min(score, 10)
    feedback = f"Score {score}/10 — {word_count} woorden onderscheidend vermogen."

    return score, feedback, suggestions


def _score_audience_fit(intake: ProfileIntake) -> tuple:
    score = 0
    suggestions = []

    if not intake.target_audience.strip():
        # Geen doelgroep bekend — geef neutrale score (niet hard penaliseren bij PDF)
        return 5, "Doelgroep automatisch bepaald.", [
            "Tip: definieer specifiek wie je wilt bereiken voor betere positionering"
        ]

    # Check of headline past bij doel
    goal = intake.linkedin_goal
    headline = intake.current_headline.lower()

    if goal == "Een nieuwe baan vinden" or goal == "Gerekruteerd worden door recruiters":
        if any(w in headline for w in ["zoek", "open", "beschikbaar"]):
            score += 3
        else:
            score += 1
            suggestions.append("Als je een baan zoekt, overweeg 'Open voor nieuwe kansen' in je headline")

    elif goal == "Meer klanten / opdrachten krijgen":
        if any(w in headline for w in ["help", "specialist", "oploss", "dienst"]):
            score += 3
        else:
            score += 1
            suggestions.append("Voor klantwerving: positioneer jezelf als oplossing, niet als werkzoekende")

    else:
        score += 2

    # Doelgroep specifiek genoeg?
    audience = intake.target_audience.strip()
    if len(audience.split()) >= 5:
        score += 3
    else:
        score += 1
        suggestions.append("Wees specifieker over je doelgroep: welke functietitels, sectoren, bedrijfsgrootte?")

    # Skills passen bij doelgroep?
    skills = intake.parse_skills_list()
    if len(skills) >= 3:
        score += 4
    else:
        score += 2

    score = min(score, 10)
    feedback = f"Score {score}/10 — Doel: {goal}, doelgroep gedefinieerd."

    return score, feedback, suggestions


# ============================================================
# HELPERS
# ============================================================

def _get_sector_keywords(sector: str) -> list:
    """Haal sector-specifieke keywords op."""
    for key, keywords in SECTOR_KEYWORDS.items():
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            return keywords
    return DEFAULT_KEYWORDS


def _generate_summary(total_score: int, intake: ProfileIntake) -> str:
    """Genereer een samenvattende tekst op basis van de totaalscore."""
    name = intake.full_name

    if total_score >= 85:
        return (f"Uitstekend, {name}! Je profiel scoort {total_score}/100. "
                f"Je hebt een sterk profiel dat goed vindbaar is. "
                f"Met enkele verfijningen kun je nog meer impact maken.")
    elif total_score >= 70:
        return (f"Goed werk, {name}! Je profiel scoort {total_score}/100. "
                f"Je hebt een solide basis, maar er liggen kansen om je zichtbaarheid en "
                f"conversie significant te verbeteren.")
    elif total_score >= 55:
        return (f"{name}, je profiel scoort {total_score}/100. "
                f"Er is ruimte voor verbetering op meerdere vlakken. "
                f"Met de aanbevelingen hieronder kun je je score naar 80+ tillen.")
    elif total_score >= 40:
        return (f"{name}, je profiel scoort {total_score}/100. "
                f"Je mist belangrijke elementen die recruiters en connecties verwachten. "
                f"De verbeteringen hieronder maken een groot verschil.")
    else:
        return (f"{name}, je profiel scoort {total_score}/100. "
                f"Je profiel heeft dringend aandacht nodig. "
                f"Gelukkig hebben we een compleet plan voor je klaarstaan!")


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Gebruik: python profile_scorer.py <intake.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    test_intake = ProfileIntake(**data)

    result = score_profile(test_intake)
    print(f"\n🎯 PROFIEL SCORE: {result.total_score}/100 (Grade: {result.grade})")
    print(f"📝 {result.summary}\n")

    for cat in result.categories:
        bar = "█" * cat.score + "░" * (10 - cat.score)
        print(f"  {cat.name:30s} [{bar}] {cat.score}/10 ({cat.weight_pct}%)")
        if cat.suggestions:
            for s in cat.suggestions:
                print(f"    💡 {s}")

    print(f"\n🔥 TOP VERBETERPUNTEN:")
    for imp in result.top_improvements:
        print(f"  → {imp}")
