"""
LinkedIn Profile Optimizer Agent — Hoofdscript
Voert de volledige analyse pipeline uit op basis van intake data.

Gebruik:
    python run_analysis.py <intake.json>        # Analyse van JSON intake bestand
"""

import os
import sys
import json
from datetime import datetime

from models import ProfileIntake, ProfileAnalysis, ProfileScore
from analyzer.profile_scorer import score_profile
from analyzer.storybrand_rewriter import generate_headlines, generate_about, improve_experience
from analyzer.seo_analyzer import analyze_seo, get_keyword_coverage
from generator.mockup_builder import build_mockup
from generator.banner_generator import generate_banner_from_image, generate_banner_pillow_only, generate_banner_prompt
from generator.report_builder import build_report


def run_full_analysis(intake: ProfileIntake, output_dir: str = None) -> ProfileAnalysis:
    """
    Voert de volledige analyse pipeline uit:
    1. Profiel scoring
    2. Headline generatie
    3. StoryBrand 'Over mij' herschrijving
    4. SEO keyword analyse
    5. Werkervaring verbetering
    6. Banner generatie
    7. Mockup generatie
    8. Rapport generatie
    """
    safe_name = intake.full_name.replace(" ", "_")
    if not output_dir:
        output_dir = os.path.join("output", safe_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  🚀 LINKEDIN PROFILE OPTIMIZER AGENT v2.0")
    print(f"  Analyse voor: {intake.full_name}")
    print(f"{'='*60}\n")

    # ==========================================
    # STAP 1: Profiel scoring
    # ==========================================
    print("📊 Stap 1/8: Profiel scoring...")
    profile_score = score_profile(intake)
    print(f"   ✅ Score: {profile_score.total_score}/100 (Grade {profile_score.grade})")

    # ==========================================
    # STAP 2: Headline generatie
    # ==========================================
    print("🎯 Stap 2/8: Headline opties genereren...")
    headline_options = generate_headlines(intake)
    print(f"   ✅ {len(headline_options)} headline opties gegenereerd")
    for opt in headline_options:
        print(f"      → [{opt.style}] {opt.text[:80]}...")

    # ==========================================
    # STAP 3: StoryBrand 'Over mij'
    # ==========================================
    print("📝 Stap 3/8: StoryBrand 'Over mij' genereren...")
    improved_about = generate_about(intake)
    print(f"   ✅ Nieuwe 'Over mij': {improved_about.word_count} woorden")

    # ==========================================
    # STAP 4: SEO analyse
    # ==========================================
    print("🔍 Stap 4/8: SEO keyword analyse...")
    seo_keywords = analyze_seo(intake)
    coverage = get_keyword_coverage(intake)
    print(f"   ✅ {len(seo_keywords)} ontbrekende keywords gevonden")
    print(f"   ✅ Coverage: {coverage['total_coverage']}% ({coverage['unique_found']}/{coverage['total_keywords']})")

    # ==========================================
    # STAP 5: Werkervaring verbetering
    # ==========================================
    print("💼 Stap 5/8: Werkervaring verbeteren...")
    improved_experiences = improve_experience(intake)
    print(f"   ✅ {len(improved_experiences)} ervaringen verbeterd")

    # ==========================================
    # STAP 6: Skills aanbevelingen
    # ==========================================
    print("⚡ Stap 6/8: Skills aanbevelingen...")
    current_skills = intake.parse_skills_list()
    recommended_skills = current_skills.copy()
    # Voeg ontbrekende keywords toe als skills
    for kw in seo_keywords:
        if kw.where_to_add == "skills" and kw.keyword not in recommended_skills:
            recommended_skills.append(kw.keyword)
    print(f"   ✅ {len(recommended_skills)} skills aanbevolen (was: {len(current_skills)})")

    # ==========================================
    # Bouw ProfileAnalysis object
    # ==========================================
    action_items = _generate_action_items(intake, profile_score, seo_keywords)
    expected_results = _calculate_expected_results(profile_score.total_score, intake.linkedin_goal)

    analysis = ProfileAnalysis(
        created_at=datetime.now(),
        intake=intake,
        score=profile_score,
        headline_options=headline_options,
        improved_about=improved_about,
        seo_keywords=seo_keywords,
        improved_experiences=improved_experiences,
        recommended_skills=recommended_skills,
        banner_prompt=generate_banner_prompt(intake),
        action_items=action_items,
        expected_results=expected_results,
    )

    # ==========================================
    # STAP 7: Banner generatie
    # ==========================================
    print("🎨 Stap 7/8: Banner genereren...")
    try:
        # Probeer eerst een AI-gegenereerde achtergrond te gebruiken
        # (als die al eerder is gegenereerd en doorgegeven)
        ai_bg_path = getattr(intake, '_ai_banner_background', None)
        if ai_bg_path and os.path.exists(ai_bg_path):
            banner_path = generate_banner_from_image(ai_bg_path, intake, output_dir)
        else:
            # Gebruik Pillow fallback
            banner_path = generate_banner_pillow_only(intake, output_dir)
            print("   ℹ️  Pillow fallback gebruikt (geen AI achtergrond beschikbaar)")
            print(f"   💡 Tip: Genereer een AI achtergrond met deze prompt:")
            print(f"      {generate_banner_prompt(intake)[:100]}...")
        analysis.banner_png_path = banner_path
        print(f"   ✅ Banner: {banner_path}")
    except Exception as e:
        print(f"   ⚠️ Banner fout: {e}")
        analysis.banner_png_path = None

    # ==========================================
    # STAP 8: Mockup + Rapport genereren
    # ==========================================
    print("📄 Stap 8/8: Mockup en rapport genereren...")
    try:
        mockup_path = build_mockup(analysis, output_dir)
        analysis.mockup_html_path = mockup_path
        print(f"   ✅ Mockup: {mockup_path}")
    except Exception as e:
        print(f"   ⚠️ Mockup fout: {e}")

    try:
        report_path = build_report(analysis, output_dir)
        analysis.report_pdf_path = report_path
        print(f"   ✅ Rapport: {report_path}")
    except Exception as e:
        print(f"   ⚠️ Rapport fout: {e}")

    # ==========================================
    # KLAAR
    # ==========================================
    print(f"\n{'='*60}")
    print(f"  ✅ ANALYSE COMPLEET — {intake.full_name}")
    print(f"{'='*60}")
    print(f"\n  📊 Score: {profile_score.total_score}/100 (Grade {profile_score.grade})")
    print(f"  📁 Output folder: {output_dir}")
    print(f"  📄 Rapport: {analysis.report_pdf_path}")
    print(f"  🖼️  Mockup: {analysis.mockup_html_path}")
    print(f"  🎨 Banner: {analysis.banner_png_path}")
    print(f"\n  🔥 Top verbeterpunten:")
    for imp in profile_score.top_improvements:
        print(f"     → {imp}")
    print()

    return analysis


def _generate_action_items(intake, score, keywords) -> list:
    """Genereert concrete actiepunten op basis van de analyse."""
    actions = []

    # Headline
    if any(c.name == "Headline / Kopregel" and c.score < 7 for c in score.categories):
        actions.append("Vervang je huidige headline door de aanbevolen optie (zie boven)")

    # Over mij
    if any(c.name == "Over Mij / About" and c.score < 5 for c in score.categories):
        actions.append("Kopieer de nieuwe 'Over mij' tekst naar je LinkedIn profiel")
    elif any(c.name == "Over Mij / About" and c.score < 8 for c in score.categories):
        actions.append("Update je 'Over mij' met de verbeterde versie")

    # Skills
    missing_skills = [kw.keyword for kw in keywords if kw.where_to_add == "skills"]
    if missing_skills:
        actions.append(f"Voeg deze skills toe: {', '.join(missing_skills[:5])}")

    # Werkervaring
    if any(c.name == "Werkervaring" and c.score < 6 for c in score.categories):
        actions.append("Vervang je werkervaring beschrijvingen door de verbeterde versies")

    # Foto
    if any(c.name == "Profielfoto" and c.score < 5 for c in score.categories):
        actions.append("Upload een professionele profielfoto (gezicht duidelijk, neutrale achtergrond)")

    # SEO
    if any(c.name == "SEO & Keywords" and c.score < 6 for c in score.categories):
        actions.append("Verwerk de aanbevolen keywords in je headline, about en ervaring secties")

    # Generiek
    actions.append("Vraag 3-5 collega's om je vaardigheden te endorsen")
    actions.append("Deel de komende 2 weken minimaal 2 posts over je vakgebied")

    return actions


def _calculate_expected_results(score: int, goal: str) -> dict:
    """Berekent verwachte resultaten VOOR en NA optimalisatie."""
    # Huidige geschatte waarden (op basis van de lage score)
    before_views = max(5, score // 3)
    before_connections = max(1, score // 15)
    before_messages = max(0, score // 30)

    # Na optimalisatie (geprojecteerd)
    after_views = 80 + (score * 2)
    after_connections = 15 + (score // 4)
    after_messages = 3 + (score // 12)

    if goal in ["Een nieuwe baan vinden", "Gerekruteerd worden door recruiters"]:
        after_messages += 3
        after_connections += 5

    return {
        "views_before": before_views,
        "views_after": after_views,
        "views_increase": f"+{after_views - before_views}",
        "connections_before": before_connections,
        "connections_after": after_connections,
        "connections_increase": f"+{after_connections - before_connections}",
        "messages_before": before_messages,
        "messages_after": after_messages,
        "messages_increase": f"+{after_messages - before_messages}",
        "search_before": "Niet zichtbaar",
        "search_after": "Top 20%",
        "search_increase": "+200%",
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Gebruik: python run_analysis.py <intake.json>")
        print("   Maak een JSON bestand aan met ProfileIntake velden.")
        print("   Of gebruik de webhook: python webhook_handler.py")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    intake = ProfileIntake(**data)
    analysis = run_full_analysis(intake)
