"""
StoryBrand Rewriter (SB7 Framework)
Genereert verbeterde LinkedIn profielteksten op basis van het StoryBrand framework.
Gebruikt de bestaande patronen uit StoryBrand_Blueprint.md en 1_Profiel_Optimalisatie.md.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProfileIntake, HeadlineOption, ImprovedAbout, ImprovedExperience


# ============================================================
# HEADLINE GENERATOR — 3 opties per profiel
# ============================================================

def generate_headlines(intake: ProfileIntake) -> list[HeadlineOption]:
    """
    Genereert 3 headline opties gebaseerd op het bewezen patroon:
    1. Direct & Probleemoplossend (Aanbevolen)
    2. Resultaatgericht
    3. Kort & Autoriteit
    """
    name = intake.full_name
    title = intake.current_job_title
    sector = intake.target_sector
    years = intake.years_experience
    location = intake.location.split(",")[1].strip() if "," in intake.location else intake.location
    employer = intake.current_employer
    goal = intake.linkedin_goal
    unique = intake.unique_value
    skills_text = intake.top_3_skills

    # Parse jaren als getal
    years_num = _extract_years(years)

    # Goal-specifieke elementen
    if goal in ["Een nieuwe baan vinden", "Gerekruteerd worden door recruiters"]:
        goal_suffix = f"| Open voor nieuwe uitdagingen in {location}"
        goal_cta = f"| Beschikbaar voor {sector}"
    elif goal in ["Meer klanten / opdrachten krijgen"]:
        goal_suffix = f"| Ik help bedrijven in {sector}"
        goal_cta = f"| Neem contact op"
    else:
        goal_suffix = f"| {location}"
        goal_cta = ""

    # Eerste skill als specialisatie (pak alleen de eerste, niet de hele lijst)
    first_skill = ""
    if skills_text:
        parts = [s.strip() for s in skills_text.replace("\n", ",").split(",") if s.strip()]
        first_skill = parts[0] if parts else title
    else:
        first_skill = title

    options = []

    # Optie 1: Direct & Probleemoplossend (Aanbevolen)
    if years_num:
        opt1 = f"{title} | {first_skill} | {years_num}+ jaar {sector}" if sector else f"{title} | {first_skill} | {years_num}j ervaring"
    else:
        opt1 = f"{title} | {first_skill} {goal_suffix}"
    options.append(HeadlineOption(
        style="Direct & Probleemoplossend",
        text=opt1.strip(),
        explanation="Combineert je functietitel, specialisme, ervaring en locatie. "
                    "Bevat de belangrijkste zoektermen direct in de headline."
    ))

    # Optie 2: Resultaatgericht
    if goal in ["Een nieuwe baan vinden", "Gerekruteerd worden door recruiters"]:
        opt2 = (f"{title} bij {employer} | "
                f"{years_num}+ jaar ervaring in {sector} | "
                f"Open voor nieuwe kansen in {location}")
    else:
        opt2 = (f"{title} | {_generate_value_hook(intake)} | "
                f"{employer}")
    options.append(HeadlineOption(
        style="Resultaatgericht",
        text=opt2.strip(),
        explanation="Legt nadruk op je resultaten en wat je hebt bereikt. "
                    "Trekt recruiters en beslissers aan die impact zoeken."
    ))

    # Optie 3: Kort & Autoriteit
    opt3 = f"{title} bij {employer} | {_generate_authority_tag(intake)} | {location}"
    options.append(HeadlineOption(
        style="Kort & Autoriteit",
        text=opt3.strip(),
        explanation="Compact en autoritair. Positioneert je direct als expert "
                    "met duidelijke organisatie en locatie."
    ))

    return options


# ============================================================
# ABOUT / OVER MIJ GENERATOR — StoryBrand SB7
# ============================================================

def generate_about(intake: ProfileIntake) -> ImprovedAbout:
    """
    Genereert een verbeterde 'Over mij' tekst op basis van het StoryBrand SB7 framework.
    Structuur: Probleem → Gids (empathie + autoriteit) → Plan → Resultaat → CTA
    """
    name = intake.full_name
    title = intake.current_job_title
    employer = intake.current_employer
    sector = intake.target_sector
    years_num = _extract_years(intake.years_experience)
    goal = intake.linkedin_goal
    unique = intake.unique_value
    skills = intake.top_3_skills
    audience = intake.target_audience
    description = intake.current_job_description

    # Bepaal de vertelling op basis van het doel
    if goal in ["Een nieuwe baan vinden", "Gerekruteerd worden door recruiters"]:
        about_text = _generate_job_seeker_about(intake, years_num)
    elif goal in ["Meer klanten / opdrachten krijgen"]:
        about_text = _generate_business_about(intake, years_num)
    else:
        about_text = _generate_branding_about(intake, years_num)

    sections = {
        "problem_external": "De marktsituatie / het probleem",
        "problem_internal": "De frustratie die dit veroorzaakt",
        "guide_empathy": "Herkenning en begrip",
        "guide_authority": "Expertise en track record",
        "plan": "Concrete stappen / aanpak",
        "call_to_action": "Wat de lezer moet doen",
        "success_result": "Het gewenste resultaat"
    }

    return ImprovedAbout(
        full_text=about_text,
        word_count=len(about_text.split()),
        sections=sections
    )


def _generate_job_seeker_about(intake: ProfileIntake, years: int) -> str:
    """StoryBrand 'Over mij' voor iemand die een baan zoekt."""
    title = intake.current_job_title
    employer = intake.current_employer
    sector = intake.target_sector
    skills = intake.top_3_skills
    unique = intake.unique_value
    description = intake.current_job_description
    location = intake.location
    audience = intake.target_audience

    text = f"""{title}
{years}+ jaar technische ervaring | {sector}

**WAT IK DOE:**
{_bullet_format(description)}

**WAAROM IK:**
{unique}

Met {years}+ jaar ervaring in {sector.lower()} breng ik een combinatie van technische diepgang en praktijkervaring mee die direct waarde toevoegt aan je organisatie.

**MIJN EXPERTISE:**
{_bullet_format(skills)}

**WAT IK ZOEK:**
Ik ben op zoek naar een uitdagende rol als {title} binnen {sector.lower()} in de regio {location}. Een organisatie waar ik mijn expertise kan inzetten en verder kan ontwikkelen.

**KERNWOORDEN:**
{_generate_keyword_line(intake)}

📩 Interesse? Stuur me een bericht of connectieverzoek — ik sta open voor een goed gesprek."""

    return text


def _generate_business_about(intake: ProfileIntake, years: int) -> str:
    """StoryBrand 'Over mij' voor een ondernemer/freelancer die klanten zoekt."""
    title = intake.current_job_title
    employer = intake.current_employer
    sector = intake.target_sector
    skills = intake.top_3_skills
    unique = intake.unique_value
    audience = intake.target_audience

    text = f"""**Heb je moeite om de juiste {_audience_problem(intake)} te vinden? Je bent niet de enige.**

In de huidige markt zie ik dagelijks bedrijven in {sector.lower()} worstelen met dezelfde uitdaging. {_sector_pain_point(intake)}

Ik ben {intake.first_name}, {title} bij {employer}. Al {years}+ jaar werk ik in {sector.lower()}, en wat ik anders doe dan de rest? {unique}

**Mijn aanpak in 3 stappen:**
1. **Analyse:** We brengen de exacte situatie in kaart
2. **Strategie:** Op basis van data en ervaring bepalen we de beste route
3. **Uitvoering:** Ik lever resultaat, geen beloftes

**Het resultaat:**
✅ Een oplossing die daadwerkelijk werkt
✅ Gefundeerd op {years}+ jaar praktijkervaring
✅ Geen standaard aanpak, maar maatwerk

📩 Stuur me een DM of mail naar {intake.email} voor een vrijblijvend kennismakingsgesprek.

**Specialisaties:** {_generate_keyword_line(intake)}"""

    return text


def _generate_branding_about(intake: ProfileIntake, years: int) -> str:
    """StoryBrand 'Over mij' voor personal branding / netwerk."""
    title = intake.current_job_title
    employer = intake.current_employer
    sector = intake.target_sector
    unique = intake.unique_value
    skills = intake.top_3_skills

    text = f"""{title} | {sector}

Met {years}+ jaar ervaring in {sector.lower()} heb ik een duidelijke visie ontwikkeld op hoe dit vakgebied zich ontwikkelt. {unique}

**EXPERTISE:**
{_bullet_format(skills)}

**HUIDIGE ROL:**
Als {title} bij {employer} ben ik verantwoordelijk voor:
{_bullet_format(intake.current_job_description)}

**VISIE:**
Ik geloof dat de toekomst van {sector.lower()} ligt in de combinatie van ervaring en innovatie. Door kennis te delen en samen te werken, kunnen we het vakgebied naar een hoger niveau tillen.

**KERNWOORDEN:**
{_generate_keyword_line(intake)}

🔗 Open voor verbindingen met professionals in {sector.lower()}. Stuur me gerust een connectieverzoek!"""

    return text


# ============================================================
# EXPERIENCE IMPROVER
# ============================================================

def improve_experience(intake: ProfileIntake) -> list[ImprovedExperience]:
    """Verbetert de werkervaring beschrijvingen met structuur en resultaten."""
    experiences = []

    # Huidige functie
    current = ImprovedExperience(
        company=intake.current_employer,
        title=intake.current_job_title,
        period=f"{intake.current_job_start} - heden",
        original_description=intake.current_job_description,
        improved_description=_improve_job_description(
            intake.current_job_description,
            intake.current_job_title,
            intake.current_employer
        ),
        key_improvements=[]
    )

    # Bepaal verbeteringen
    original = intake.current_job_description
    if len(original.split()) < 50:
        current.key_improvements.append("Beschrijving uitgebreid van kort naar volledig")
    if not any(c in original for c in ["•", "✅", "-"]):
        current.key_improvements.append("Structuur toegevoegd met bulletpoints")
    import re
    if not re.search(r'\d+', original):
        current.key_improvements.append("Concrete getallen en resultaten toegevoegd")
    if "RESULTAAT" not in original.upper():
        current.key_improvements.append("Resultaten-sectie toegevoegd")

    experiences.append(current)

    # Eerdere ervaring
    for exp in intake.parse_experience_items():
        prev = ImprovedExperience(
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            period=exp.get("period", ""),
            original_description=exp.get("description", ""),
            improved_description=_improve_job_description(
                exp.get("description", ""),
                exp.get("title", ""),
                exp.get("company", "")
            ),
            key_improvements=["Beschrijving uitgebreid", "Structuur verbeterd"]
        )
        experiences.append(prev)

    return experiences


def _improve_job_description(description: str, title: str, company: str) -> str:
    """Verbetert een individuele werkervaring beschrijving."""
    if not description or len(description.strip().split()) < 10:
        # Genereer een basis beschrijving
        return f"""**KERNTAKEN:**
• {title} bij {company}
• Dagelijkse verantwoordelijkheden in lijn met de functie
• Samenwerking met interne en externe stakeholders

**RESULTAAT:**
✅ Bijgedragen aan de doelstellingen van {company}
✅ Kennis en ervaring opgedaan in het vakgebied

💡 *Tip: Voeg hier concrete getallen, projecten en resultaten toe!*"""

    # Verbeter bestaande beschrijving
    lines = description.strip().split("\n")
    improved_lines = []
    has_kerntaken = False
    has_resultaat = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "KERNTAKEN" in line.upper() or "TAKEN" in line.upper():
            has_kerntaken = True
        if "RESULTAAT" in line.upper():
            has_resultaat = True

        # Voeg bulletpoint toe als die er niet is
        if not line.startswith("•") and not line.startswith("-") and not line.startswith("✅"):
            if not any(line.upper().startswith(h) for h in ["KERNTAKEN", "RESULTAAT", "**"]):
                line = f"• {line}"
        improved_lines.append(line)

    # Voeg structuur toe als die ontbreekt
    result = ""
    if not has_kerntaken:
        result += "**KERNTAKEN:**\n"
    result += "\n".join(improved_lines)
    if not has_resultaat:
        result += "\n\n**RESULTAAT:**\n✅ Succesvol bijgedragen aan de organisatiedoelen\n✅ Expertise verder ontwikkeld"

    return result


# ============================================================
# HELPERS
# ============================================================

def _extract_years(years_str: str) -> int:
    """Extraheert een getal uit de ervaringsbeschrijving."""
    import re
    match = re.search(r'(\d+)', years_str)
    if match:
        return int(match.group(1))
    return 10  # Fallback


def _bullet_format(text: str) -> str:
    """Formatteert tekst als bulletpoints."""
    if not text:
        return "• (nog in te vullen)"

    lines = text.strip().split("\n")
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not line.startswith("•") and not line.startswith("-") and not line.startswith("✅"):
            if not line.startswith("1.") and not line.startswith("2.") and not line.startswith("3."):
                line = f"• {line}"
        formatted.append(line)
    return "\n".join(formatted)


def _generate_value_hook(intake: ProfileIntake) -> str:
    """Genereert een korte waarde-hook."""
    unique = intake.unique_value
    if unique and len(unique) > 20:
        # Gebruik eerste zin
        first_sentence = unique.split(".")[0].strip()
        if len(first_sentence) <= 80:
            return first_sentence
    return f"Specialist in {intake.target_sector}"


def _generate_authority_tag(intake: ProfileIntake) -> str:
    """Genereert een autoriteit-tag."""
    years = _extract_years(intake.years_experience)
    sector = intake.target_sector
    return f"{years}+ jaar {sector}"


def _generate_keyword_line(intake: ProfileIntake) -> str:
    """Genereert een keyword-regel voor onderaan de 'Over mij'."""
    skills = intake.parse_skills_list()
    if skills:
        return " • ".join(skills[:8])
    return intake.current_job_title


def _audience_problem(intake: ProfileIntake) -> str:
    """Genereert een doelgroep-probleem beschrijving."""
    sector = intake.target_sector
    audience = intake.target_audience
    if audience:
        return audience.split(",")[0].strip().lower()
    return f"professionals in {sector.lower()}"


def _sector_pain_point(intake: ProfileIntake) -> str:
    """Genereert een sector-specifiek pijnpunt."""
    pain_points = {
        "Bouw & Infra": "Projecten lopen vertraging op, het team staat onder druk, en de juiste vakmensen zijn schaars.",
        "Techniek & Industrie": "De markt is krapper dan ooit. Technisch talent heeft het voor het uitkiezen.",
        "IT & Software": "Elke developer krijgt dagelijks 5+ recruiter-berichten. Opvallen is een uitdaging.",
        "Overheid & Publieke Sector": "De publieke sector concurreert steeds vaker met het bedrijfsleven om talent.",
        "Engineering & R&D": "Innovatie staat of valt met de juiste engineers. Die zijn helaas schaars.",
    }
    for key, point in pain_points.items():
        if key.lower() in intake.target_sector.lower():
            return point
    return "De arbeidsmarkt verandert snel en de juiste mensen vinden wordt steeds uitdagender."


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    import json, sys
    from models import ProfileIntake

    if len(sys.argv) < 2:
        print("Gebruik: python storybrand_rewriter.py <intake.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    test = ProfileIntake(**data)

    print("=" * 60)
    print("📝 HEADLINE OPTIES")
    print("=" * 60)
    for opt in generate_headlines(test):
        print(f"\n🔹 {opt.style}:")
        print(f"   \"{opt.text}\"")
        print(f"   → {opt.explanation}")

    print("\n" + "=" * 60)
    print("📄 VERBETERDE 'OVER MIJ'")
    print("=" * 60)
    about = generate_about(test)
    print(f"\n{about.full_text}")
    print(f"\n(Woordentelling: {about.word_count})")

    print("\n" + "=" * 60)
    print("💼 VERBETERDE WERKERVARING")
    print("=" * 60)
    for exp in improve_experience(test):
        print(f"\n🏢 {exp.company} — {exp.title}")
        print(f"   Origineel: {exp.original_description[:80]}...")
        print(f"   Verbeterd:\n{exp.improved_description}")
        print(f"   Verbeteringen: {', '.join(exp.key_improvements)}")
