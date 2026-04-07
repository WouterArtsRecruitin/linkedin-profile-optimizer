"""
Report Builder
Genereert hosted rapport HTML en email summary via Jinja2 templates.
"""

import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jinja2 import Environment, FileSystemLoader
from models import ProfileAnalysis

# Jinja2 environment
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=False)


def _score_color(pct: float) -> str:
    if pct >= 70:
        return "#22c55e"
    elif pct >= 50:
        return "#eab308"
    elif pct >= 30:
        return "#f97316"
    return "#ef4444"


def _score_label(score: int) -> str:
    if score >= 80:
        return "Sterk profiel"
    elif score >= 60:
        return "Goed, met ruimte voor groei"
    elif score >= 40:
        return "Veel potentieel"
    return "Profiel heeft aandacht nodig"


def _build_categories(score) -> list:
    cats = []
    for cat in score.categories:
        pct = int((cat.score / cat.max_score) * 100) if cat.max_score else 0
        cats.append({
            "name": cat.name,
            "score": cat.score,
            "max_score": cat.max_score,
            "pct": pct,
            "color": _score_color(pct),
            "suggestions": cat.suggestions or [],
        })
    return cats


def _md_to_html(text: str) -> str:
    """Convert markdown bold to HTML strong tags."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    return text.replace("\n", "<br>")


def build_hosted_rapport(analysis: ProfileAnalysis, mockup_url: str = "") -> str:
    """Render hosted rapport HTML via Jinja2 template."""
    score = analysis.score
    intake = analysis.intake
    total = score.total_score
    categories = _build_categories(score)

    about_text = ""
    about_word_count = 0
    if analysis.improved_about and analysis.improved_about.full_text:
        about_text = _md_to_html(analysis.improved_about.full_text)
        about_word_count = analysis.improved_about.word_count

    template = _jinja_env.get_template("hosted_rapport.html")
    return template.render(
        name=intake.full_name,
        job_title=intake.current_job_title or "",
        total_score=total,
        grade=score.grade,
        score_color=_score_color(total),
        score_pct=total,
        score_label=_score_label(total),
        score_summary=score.summary or "",
        categories=categories,
        current_headline=intake.current_headline or "",
        headlines=[
            {"style": h.style, "text": h.text, "explanation": h.explanation}
            for h in (analysis.headline_options or [])
        ],
        about_text=about_text,
        about_word_count=about_word_count,
        keywords=[
            {"keyword": k.keyword, "relevance_score": k.relevance_score, "where_to_add": k.where_to_add}
            for k in (analysis.seo_keywords or [])
        ],
        experiences=[
            {
                "company": e.company, "title": e.title,
                "original_description": e.original_description or "(leeg)",
                "improved_description": e.improved_description,
            }
            for e in (analysis.improved_experiences or [])
        ],
        actions=analysis.action_items or [],
        mockup_url=mockup_url,
        year=datetime.now().year,
    )


def build_email_summary(
    analysis: ProfileAnalysis,
    rapport_url: str = "",
    mockup_url: str = "",
) -> str:
    """Render premium email summary via Jinja2 template."""
    score = analysis.score
    intake = analysis.intake
    total = score.total_score
    categories = _build_categories(score)

    # Top 3 categories sorted by weight
    top_cats = sorted(categories, key=lambda c: c["pct"])[:3]

    recommended = None
    if analysis.headline_options:
        h = analysis.headline_options[0]
        recommended = {"text": h.text, "explanation": h.explanation}

    # Short summary (first sentence)
    summary_short = (score.summary or "").split(".")[0] + "." if score.summary else ""

    template = _jinja_env.get_template("email_rapport.html")
    return template.render(
        name=intake.full_name,
        total_score=total,
        score_color=_score_color(total),
        score_label=_score_label(total),
        score_summary_short=summary_short,
        top_categories=top_cats,
        recommended_headline=recommended,
        mockup_url=mockup_url,
        rapport_url=rapport_url,
    )


def build_report(analysis: ProfileAnalysis, output_dir: str = "./output") -> str:
    """
    Genereert een compleet HTML analyserapport.
    Retourneert het pad naar het gegenereerde HTML bestand.
    """
    os.makedirs(output_dir, exist_ok=True)
    intake = analysis.intake
    score = analysis.score

    # Score kleur bepalen
    if score.total_score >= 80:
        score_color = "#16a34a"
        score_bg = "#dcfce7"
    elif score.total_score >= 60:
        score_color = "#d97706"
        score_bg = "#fef3c7"
    elif score.total_score >= 40:
        score_color = "#ea580c"
        score_bg = "#ffedd5"
    else:
        score_color = "#dc2626"
        score_bg = "#fee2e2"

    # Bouw het rapport
    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkedIn Analyse — {intake.full_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
        }}

        /* Header */
        .report-header {{
            background: linear-gradient(135deg, #0a66c2 0%, #004182 100%);
            color: white;
            padding: 48px 24px;
            text-align: center;
        }}
        .report-header h1 {{ font-size: 32px; margin-bottom: 8px; }}
        .report-header p {{ font-size: 16px; opacity: 0.9; }}
        .report-header .date {{ font-size: 13px; opacity: 0.7; margin-top: 12px; }}

        /* Container */
        .container {{ max-width: 900px; margin: 0 auto; padding: 32px 24px; }}

        /* Score card */
        .score-card {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 32px;
        }}
        .score-circle {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .score-number {{ font-size: 48px; font-weight: 800; }}
        .score-grade {{ font-size: 14px; font-weight: 600; opacity: 0.8; }}
        .score-summary {{ font-size: 15px; color: #475569; }}

        /* Section */
        .section {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            font-size: 22px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* Score bars */
        .score-bar-container {{ margin-bottom: 16px; }}
        .score-bar-label {{
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 6px;
        }}
        .score-bar {{
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .score-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        .bar-green {{ background: #16a34a; }}
        .bar-yellow {{ background: #d97706; }}
        .bar-orange {{ background: #ea580c; }}
        .bar-red {{ background: #dc2626; }}
        .score-suggestions {{
            font-size: 13px;
            color: #64748b;
            margin-top: 6px;
            padding-left: 16px;
        }}

        /* Headline options */
        .headline-option {{
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
        }}
        .headline-option.recommended {{
            border-color: #0a66c2;
            background: #eff6ff;
        }}
        .headline-style {{
            font-size: 12px;
            font-weight: 600;
            color: #0a66c2;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .headline-text {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #0f172a;
        }}
        .headline-explain {{ font-size: 13px; color: #64748b; }}

        /* About section */
        .about-improved {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            padding: 24px;
            white-space: pre-line;
            font-size: 14px;
            line-height: 1.7;
        }}

        /* Keywords */
        .keyword-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
        }}
        .keyword-item {{
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
        }}
        .keyword-critical {{
            background: #fee2e2;
            border: 1px solid #fecaca;
        }}
        .keyword-recommended {{
            background: #fef3c7;
            border: 1px solid #fde68a;
        }}
        .keyword-where {{
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }}

        /* Action items */
        .action-list {{ list-style: none; }}
        .action-list li {{
            padding: 12px 16px;
            border-left: 3px solid #0a66c2;
            margin-bottom: 8px;
            background: #f8fafc;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
        }}
        .action-list li strong {{ color: #0a66c2; }}

        /* Experience comparison */
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .comparison-card {{
            padding: 16px;
            border-radius: 8px;
            font-size: 13px;
            white-space: pre-line;
        }}
        .comparison-before {{
            background: #fee2e2;
            border: 1px solid #fecaca;
        }}
        .comparison-after {{
            background: #dcfce7;
            border: 1px solid #bbf7d0;
        }}
        .comparison-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        /* Mockup embed */
        .mockup-frame {{
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .mockup-frame img {{
            width: 100%;
            display: block;
        }}

        /* Footer */
        .report-footer {{
            background: linear-gradient(135deg, #0a66c2 0%, #004182 100%);
            color: white;
            padding: 48px 24px;
            text-align: center;
            border-radius: 16px;
            margin-top: 32px;
        }}
        .report-footer h3 {{ font-size: 24px; margin-bottom: 12px; }}
        .report-footer p {{ opacity: 0.9; font-size: 15px; }}
        .report-footer a {{ color: #93c5fd; }}

        /* Expected results table */
        .results-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .results-table th {{
            background: #f1f5f9;
            padding: 12px 16px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
        }}
        .results-table td {{
            padding: 12px 16px;
            border-top: 1px solid #e2e8f0;
            font-size: 14px;
        }}
        .results-table .metric-up {{
            color: #16a34a;
            font-weight: 600;
        }}

        @media (max-width: 768px) {{
            .score-card {{ flex-direction: column; text-align: center; }}
            .comparison {{ grid-template-columns: 1fr; }}
            .keyword-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

    <!-- Header -->
    <div class="report-header">
        <h1>LinkedIn Profiel Analyse</h1>
        <p>{intake.full_name} — {intake.current_job_title}</p>
        <div class="date">Gegenereerd op {analysis.created_at.strftime('%d %B %Y')} door Recruitin LinkedIn Optimizer</div>
    </div>

    <div class="container">

        <!-- Score Overzicht -->
        <div class="score-card">
            <div class="score-circle" style="background: {score_bg}; color: {score_color};">
                <div class="score-number">{score.total_score}</div>
                <div class="score-grade">Grade {score.grade}</div>
            </div>
            <div class="score-summary">
                <h2 style="margin-bottom: 8px;">{score.summary.split('.')[0]}.</h2>
                <p>{''.join(score.summary.split('.')[1:])}</p>
            </div>
        </div>

        <!-- Score Breakdown -->
        <div class="section">
            <h2>📊 Score Breakdown</h2>
            {_render_score_bars(score)}
        </div>

        <!-- Headline Opties -->
        <div class="section">
            <h2>🎯 Verbeterde Headline Opties</h2>
            <p style="font-size: 14px; color: #64748b; margin-bottom: 16px;">
                Je huidige headline: <strong style="color: #dc2626;">"{intake.current_headline}"</strong>
            </p>
            {_render_headlines(analysis.headline_options)}
        </div>

        <!-- Verbeterde Over Mij -->
        <div class="section">
            <h2>📝 Verbeterde 'Over Mij' Tekst</h2>
            <p style="font-size: 13px; color: #64748b; margin-bottom: 16px;">
                Gebaseerd op het StoryBrand SB7 Framework — kopieer en plak dit in je LinkedIn profiel.
            </p>
            <div class="about-improved">{analysis.improved_about.full_text if analysis.improved_about else 'Wordt gegenereerd...'}</div>
            <p style="font-size: 12px; color: #64748b; margin-top: 8px;">
                Woordentelling: {analysis.improved_about.word_count if analysis.improved_about else 0} woorden
            </p>
        </div>

        <!-- SEO Keywords -->
        <div class="section">
            <h2>🔍 SEO Keyword Aanbevelingen</h2>
            <p style="font-size: 14px; color: #64748b; margin-bottom: 16px;">
                Deze keywords ontbreken in je profiel en zijn essentieel voor vindbaarheid in je sector.
            </p>
            <div class="keyword-grid">
                {_render_keywords(analysis.seo_keywords)}
            </div>
        </div>

        <!-- Werkervaring Vergelijking -->
        <div class="section">
            <h2>💼 Verbeterde Werkervaring</h2>
            {_render_experience_comparison(analysis.improved_experiences)}
        </div>

        <!-- Aanbevolen Skills -->
        <div class="section">
            <h2>⚡ Aanbevolen Vaardigheden</h2>
            <p style="font-size: 14px; color: #64748b; margin-bottom: 16px;">
                Huidige skills: <em>{intake.current_skills}</em>
            </p>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                {_render_skills(analysis.recommended_skills)}
            </div>
        </div>

        <!-- Concrete Actiepunten -->
        <div class="section">
            <h2>✅ Concrete Actiepunten</h2>
            <ul class="action-list">
                {_render_actions(analysis.action_items)}
            </ul>
        </div>

        <!-- Verwachte Resultaten -->
        <div class="section">
            <h2>📈 Verwachte Resultaten (30 dagen)</h2>
            {_render_expected_results(analysis.expected_results)}
        </div>

        <!-- Banner -->
        {'<div class="section"><h2>🎨 Nieuwe LinkedIn Banner</h2><div class="mockup-frame"><img src="' + (analysis.banner_png_path or '') + '" alt="LinkedIn Banner"></div></div>' if analysis.banner_png_path else ''}

        <!-- Footer -->
        <div class="report-footer">
            <h3>🚀 Klaar om je profiel te upgraden?</h3>
            <p>Wil je hulp bij de implementatie of heb je vragen over de analyse?<br>
            Neem contact op: <a href="mailto:wouter@recruitin.nl">wouter@recruitin.nl</a> |
            <a href="https://recruitin.nl">recruitin.nl</a></p>
        </div>

    </div>
</body>
</html>"""

    safe_name = intake.full_name.replace(" ", "_")
    output_path = os.path.join(output_dir, f"{safe_name}_LinkedIn_Analyse.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Rapport gegenereerd: {output_path}")
    return output_path


# ============================================================
# RENDER HELPERS
# ============================================================

def _render_score_bars(score) -> str:
    html = ""
    for cat in score.categories:
        pct = (cat.score / cat.max_score) * 100
        if pct >= 70:
            bar_class = "bar-green"
        elif pct >= 50:
            bar_class = "bar-yellow"
        elif pct >= 30:
            bar_class = "bar-orange"
        else:
            bar_class = "bar-red"

        sug = ""
        if cat.suggestions:
            sug = '<div class="score-suggestions">' + '<br>'.join(f'💡 {s}' for s in cat.suggestions) + '</div>'

        html += f'''
        <div class="score-bar-container">
            <div class="score-bar-label">
                <span>{cat.name}</span>
                <span>{cat.score}/{cat.max_score} ({cat.weight_pct}%)</span>
            </div>
            <div class="score-bar">
                <div class="score-bar-fill {bar_class}" style="width: {pct}%;"></div>
            </div>
            {sug}
        </div>'''
    return html


def _render_headlines(options) -> str:
    html = ""
    for i, opt in enumerate(options):
        rec = " recommended" if i == 0 else ""
        badge = ' <span style="background:#0a66c2;color:white;padding:2px 8px;border-radius:4px;font-size:11px;">AANBEVOLEN</span>' if i == 0 else ""
        html += f'''
        <div class="headline-option{rec}">
            <div class="headline-style">{opt.style}{badge}</div>
            <div class="headline-text">{opt.text}</div>
            <div class="headline-explain">{opt.explanation}</div>
        </div>'''
    return html


def _render_keywords(keywords) -> str:
    html = ""
    for kw in keywords:
        css_class = "keyword-critical" if kw.relevance_score >= 9 else "keyword-recommended"
        html += f'''
        <div class="keyword-item {css_class}">
            <strong>{kw.keyword}</strong>
            <div class="keyword-where">➡️ Toevoegen aan: {kw.where_to_add}</div>
        </div>'''
    return html


def _render_experience_comparison(experiences) -> str:
    html = ""
    for exp in experiences:
        html += f'''
        <h3 style="margin: 16px 0 8px; font-size: 16px;">{exp.company} — {exp.title}</h3>
        <div class="comparison">
            <div class="comparison-card comparison-before">
                <div class="comparison-label" style="color: #dc2626;">❌ VOOR</div>
                {exp.original_description or '(leeg)'}
            </div>
            <div class="comparison-card comparison-after">
                <div class="comparison-label" style="color: #16a34a;">✅ NA</div>
                {exp.improved_description}
            </div>
        </div>
        <div style="font-size: 12px; color: #64748b; margin-bottom: 16px;">
            Verbeteringen: {', '.join(exp.key_improvements)}
        </div>'''
    return html


def _render_skills(skills) -> str:
    html = ""
    for skill in skills:
        html += f'<span style="background:#eef3f8;padding:6px 14px;border-radius:20px;font-size:14px;font-weight:500;">{skill}</span>\n'
    return html


def _render_actions(actions) -> str:
    html = ""
    for i, action in enumerate(actions, 1):
        html += f'<li><strong>Stap {i}:</strong> {action}</li>\n'
    return html


def _render_expected_results(results) -> str:
    if not results:
        return '<p style="color: #64748b;">Wordt berekend...</p>'

    html = '''<table class="results-table">
        <tr><th>Metric</th><th>Nu (geschat)</th><th>Na optimalisatie</th><th>Verbetering</th></tr>'''

    metrics = {
        "Profielweergaven/maand": ("views_before", "views_after", "views_increase"),
        "Verbindingsverzoeken/maand": ("connections_before", "connections_after", "connections_increase"),
        "Recruiter berichten/maand": ("messages_before", "messages_after", "messages_increase"),
        "LinkedIn zoekpositie": ("search_before", "search_after", "search_increase"),
    }

    for label, (before, after, increase) in metrics.items():
        b = results.get(before, "—")
        a = results.get(after, "—")
        inc = results.get(increase, "—")
        html += f'<tr><td>{label}</td><td>{b}</td><td><strong>{a}</strong></td><td class="metric-up">⬆️ {inc}</td></tr>\n'

    html += '</table>'
    return html
