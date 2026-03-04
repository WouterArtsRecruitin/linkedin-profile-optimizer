"""
Mockup Builder
Genereert een volledig HTML LinkedIn profiel mockup met verbeterde teksten.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
from jinja2 import Environment, FileSystemLoader
from models import ProfileIntake, ProfileAnalysis
import random


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def build_mockup(analysis: ProfileAnalysis, output_dir: str = "./output") -> str:
    """
    Bouwt een HTML mockup op basis van de analyse resultaten.
    Retourneert het pad naar het gegenereerde HTML bestand.
    """
    intake = analysis.intake
    os.makedirs(output_dir, exist_ok=True)

    # Laad template
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("linkedin_mockup.html")

    # Bepaal beste headline
    headline = analysis.headline_options[0].text if analysis.headline_options else intake.current_headline

    # Bepaal about tekst
    about_text = analysis.improved_about.full_text if analysis.improved_about else intake.current_about

    # Bouw experience items
    experiences = []
    if analysis.improved_experiences:
        for exp in analysis.improved_experiences:
            experiences.append({
                "title": exp.title,
                "company": exp.company,
                "period": exp.period,
                "description": exp.improved_description
            })
    else:
        experiences.append({
            "title": intake.current_job_title,
            "company": intake.current_employer,
            "period": f"{intake.current_job_start} - heden",
            "description": intake.current_job_description
        })

    # Bouw education items
    education_items = intake.parse_education_items()
    if not education_items:
        education_items = [{"degree": intake.education, "year": ""}]

    # Bouw skills items met gesimuleerde endorsements
    skills = intake.parse_skills_list()
    # Voeg aanbevolen skills toe
    if analysis.recommended_skills:
        for skill in analysis.recommended_skills:
            if skill not in skills:
                skills.append(skill)

    skill_items = []
    for i, skill in enumerate(skills[:12]):
        endorsements = max(70 - (i * 5), 10) + random.randint(-5, 5)
        skill_items.append({"name": skill, "endorsements": endorsements})

    # Score styling
    score = analysis.score.total_score
    if score >= 80:
        score_color = "#16a34a"
    elif score >= 60:
        score_color = "#d97706"
    elif score >= 40:
        score_color = "#ea580c"
    else:
        score_color = "#dc2626"

    # Verwachte resultaten op basis van score
    expected = _calculate_expected_results(score, intake.linkedin_goal)

    # Banner styling — gebruik absoluut pad zodat het altijd laadt
    banner_path = analysis.banner_png_path
    if banner_path:
        abs_banner = os.path.abspath(banner_path)
        if os.path.exists(abs_banner):
            # Kopieer banner naar output dir zodat alles bij elkaar staat
            banner_filename = os.path.basename(abs_banner)
            local_banner = os.path.join(output_dir, banner_filename)
            if abs_banner != os.path.abspath(local_banner):
                shutil.copy2(abs_banner, local_banner)
            banner_class = ""
            banner_style = f"background-image: url('{banner_filename}'); background-size: cover; background-position: center;"
        else:
            banner_class = "banner-default"
            banner_style = _get_sector_gradient(intake.target_sector)
    else:
        banner_class = "banner-default"
        banner_style = _get_sector_gradient(intake.target_sector)

    # Profile foto — kopieer naar output als het een lokaal bestand is
    photo_url = intake.profile_photo_url or ""
    if photo_url and os.path.exists(photo_url):
        photo_filename = os.path.basename(photo_url)
        local_photo = os.path.join(output_dir, photo_filename)
        if photo_url != os.path.abspath(local_photo):
            shutil.copy2(photo_url, local_photo)
        photo_url = photo_filename

    # Render
    html = template.render(
        full_name=intake.full_name,
        headline=headline,
        location=intake.location,
        about_text=about_text,
        experiences=experiences,
        education_items=education_items,
        skills=skill_items,
        profile_photo_url=photo_url,
        linkedin_url=intake.linkedin_url,
        total_score=score,
        grade=analysis.score.grade,
        score_color=score_color,
        banner_class=banner_class,
        banner_style=banner_style,
        expected_views=expected["views"],
        expected_views_increase=expected["views_increase"],
        expected_connections=expected["connections"],
        expected_messages=expected["messages"],
    )

    # Schrijf output
    safe_name = intake.full_name.replace(" ", "_")
    output_path = os.path.join(output_dir, f"{safe_name}_LinkedIn_Mockup.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Mockup gegenereerd: {output_path}")
    return output_path


def _calculate_expected_results(score: int, goal: str) -> dict:
    """Berekent verwachte resultaten na optimalisatie."""
    base_views = 50 + (score * 2)
    base_connections = 10 + (score // 5)
    base_messages = 2 + (score // 15)

    if goal in ["Een nieuwe baan vinden", "Gerekruteerd worden door recruiters"]:
        base_messages += 3

    return {
        "views": base_views,
        "views_increase": min(200, 50 + score),
        "connections": base_connections,
        "messages": base_messages
    }


def _get_sector_gradient(sector: str) -> str:
    """Retourneert een gradient passend bij de sector."""
    gradients = {
        "Bouw & Infra": "background: linear-gradient(135deg, #1e3a5f 0%, #2d5a3f 100%);",
        "Techniek & Industrie": "background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);",
        "IT & Software": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);",
        "Overheid & Publieke Sector": "background: linear-gradient(135deg, #1e3a5f 0%, #2f855a 100%);",
        "Engineering & R&D": "background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);",
        "HR & Recruitment": "background: linear-gradient(135deg, #0a66c2 0%, #004182 100%);",
    }
    for key, gradient in gradients.items():
        if key.lower() in sector.lower():
            return gradient
    return "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
