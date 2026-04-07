"""
Mockup Image Builder — Pillow-based LinkedIn profiel mockup PNG generator.
Genereert een visuele preview van het geoptimaliseerde LinkedIn profiel.

Gebruikt gebundelde Inter fonts en compositeert persoonlijke data
op een LinkedIn-style layout.

Output: 1200×800 PNG (full) of 600×400 PNG (email thumbnail)
"""

import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from models import ProfileAnalysis

# Dimensions
MOCKUP_WIDTH = 1200
MOCKUP_HEIGHT = 800
BANNER_HEIGHT = 280
PROFILE_PHOTO_SIZE = 120
PROFILE_PHOTO_Y = BANNER_HEIGHT - PROFILE_PHOTO_SIZE // 2

# LinkedIn colors
BG_COLOR = (243, 242, 239)  # LinkedIn background
CARD_BG = (255, 255, 255)
CARD_BORDER = (219, 219, 219)
TEXT_PRIMARY = (0, 0, 0)
TEXT_SECONDARY = (101, 101, 101)
TEXT_MUTED = (140, 140, 140)
LINKEDIN_BLUE = (10, 102, 194)
BTN_BLUE = (10, 102, 194)
BTN_WHITE_BORDER = (10, 102, 194)
BADGE_GREEN = (34, 197, 94)
BADGE_GREEN_BG = (220, 252, 231)
SCORE_ORANGE = (255, 85, 0)

# Font directory
FONT_DIR = os.path.join(os.path.dirname(__file__), "templates", "fonts")


def _load_fonts() -> dict:
    """Load Inter fonts, fallback to system fonts."""
    fonts = {}

    inter_bold = os.path.join(FONT_DIR, "Inter-Bold.ttf")
    inter_semi = os.path.join(FONT_DIR, "Inter-SemiBold.ttf")
    inter_regular = os.path.join(FONT_DIR, "Inter-Regular.ttf")

    if os.path.exists(inter_bold):
        fonts["name"] = ImageFont.truetype(inter_bold, 28)
        fonts["headline"] = ImageFont.truetype(inter_regular, 16)
        fonts["location"] = ImageFont.truetype(inter_regular, 14)
        fonts["section_title"] = ImageFont.truetype(inter_semi, 18)
        fonts["body"] = ImageFont.truetype(inter_regular, 13)
        fonts["small"] = ImageFont.truetype(inter_regular, 11)
        fonts["badge"] = ImageFont.truetype(inter_semi, 10)
        fonts["score_big"] = ImageFont.truetype(inter_bold, 36)
        fonts["score_label"] = ImageFont.truetype(inter_semi, 12)
        fonts["btn"] = ImageFont.truetype(inter_semi, 14)
    else:
        # Fallback to system fonts
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        font_file = None
        for fp in font_paths:
            if os.path.exists(fp):
                font_file = fp
                break

        if font_file:
            fonts["name"] = ImageFont.truetype(font_file, 28)
            fonts["headline"] = ImageFont.truetype(font_file, 16)
            fonts["location"] = ImageFont.truetype(font_file, 14)
            fonts["section_title"] = ImageFont.truetype(font_file, 18)
            fonts["body"] = ImageFont.truetype(font_file, 13)
            fonts["small"] = ImageFont.truetype(font_file, 11)
            fonts["badge"] = ImageFont.truetype(font_file, 10)
            fonts["score_big"] = ImageFont.truetype(font_file, 36)
            fonts["score_label"] = ImageFont.truetype(font_file, 12)
            fonts["btn"] = ImageFont.truetype(font_file, 14)
        else:
            default = ImageFont.load_default()
            for key in ["name", "headline", "location", "section_title", "body",
                         "small", "badge", "score_big", "score_label", "btn"]:
                fonts[key] = default

    return fonts


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_banner(img, draw, analysis):
    """Draw LinkedIn banner area with gradient."""
    intake = analysis.intake
    sector = intake.target_sector or ""

    # Sector-based gradient colors
    gradients = {
        "Bouw": ((30, 58, 95), (45, 85, 130)),
        "IT": ((20, 20, 60), (50, 30, 100)),
        "HR": ((25, 50, 90), (40, 75, 120)),
        "Techniek": ((30, 40, 60), (50, 65, 90)),
    }

    color_start = (25, 45, 80)
    color_end = (40, 70, 115)
    for key, (cs, ce) in gradients.items():
        if key.lower() in sector.lower():
            color_start, color_end = cs, ce
            break

    # Draw gradient
    for y in range(BANNER_HEIGHT):
        ratio = y / BANNER_HEIGHT
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(0, y), (MOCKUP_WIDTH, y)], fill=(r, g, b))


def _draw_profile_photo(img, draw):
    """Draw placeholder profile photo circle."""
    cx = 40 + PROFILE_PHOTO_SIZE // 2
    cy = PROFILE_PHOTO_Y + PROFILE_PHOTO_SIZE // 2

    # White border
    draw.ellipse(
        [cx - PROFILE_PHOTO_SIZE // 2 - 4, cy - PROFILE_PHOTO_SIZE // 2 - 4,
         cx + PROFILE_PHOTO_SIZE // 2 + 4, cy + PROFILE_PHOTO_SIZE // 2 + 4],
        fill=(255, 255, 255)
    )
    # Gray placeholder
    draw.ellipse(
        [cx - PROFILE_PHOTO_SIZE // 2, cy - PROFILE_PHOTO_SIZE // 2,
         cx + PROFILE_PHOTO_SIZE // 2, cy + PROFILE_PHOTO_SIZE // 2],
        fill=(200, 200, 200)
    )
    # Person icon (simplified)
    head_r = 18
    draw.ellipse(
        [cx - head_r, cy - 28 - head_r, cx + head_r, cy - 28 + head_r],
        fill=(170, 170, 170)
    )
    draw.pieslice(
        [cx - 30, cy - 5, cx + 30, cy + 35],
        180, 360, fill=(170, 170, 170)
    )


def _draw_badge(draw, x, y, text, fonts, bg_color=BADGE_GREEN_BG, text_color=BADGE_GREEN):
    """Draw a small badge."""
    font = fonts["badge"]
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    padding_x, padding_y = 8, 3
    _draw_rounded_rect(
        draw,
        [x, y, x + tw + padding_x * 2, y + th + padding_y * 2],
        radius=4,
        fill=bg_color
    )
    draw.text((x + padding_x, y + padding_y), text, fill=text_color, font=font)
    return tw + padding_x * 2


def _wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def build_mockup_image(analysis: ProfileAnalysis) -> bytes:
    """Generate a LinkedIn profile mockup PNG from analysis data.

    Returns PNG bytes.
    """
    intake = analysis.intake
    fonts = _load_fonts()

    # Create image
    img = Image.new("RGB", (MOCKUP_WIDTH, MOCKUP_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Banner ---
    _draw_banner(img, draw, analysis)

    # --- White card background ---
    card_top = BANNER_HEIGHT
    card_bottom = MOCKUP_HEIGHT
    draw.rectangle([0, card_top, MOCKUP_WIDTH, card_bottom], fill=CARD_BG)
    draw.line([(0, card_top), (MOCKUP_WIDTH, card_top)], fill=CARD_BORDER, width=1)

    # --- Profile photo ---
    _draw_profile_photo(img, draw)

    # --- Name + badges ---
    name = intake.full_name or "Naam"
    name_x = 40
    name_y = PROFILE_PHOTO_Y + PROFILE_PHOTO_SIZE + 16
    draw.text((name_x, name_y), name, fill=TEXT_PRIMARY, font=fonts["name"])

    # --- Headline (improved) ---
    headline = intake.current_headline or ""
    if analysis.headline_options:
        headline = analysis.headline_options[0].text

    headline_y = name_y + 36
    headline_lines = _wrap_text(headline, fonts["headline"], 700, draw)
    for i, line in enumerate(headline_lines[:2]):
        draw.text((name_x, headline_y + i * 22), line, fill=TEXT_SECONDARY, font=fonts["headline"])

    # "VERBETERD" badge next to headline
    if analysis.headline_options:
        badge_x = name_x + draw.textbbox((0, 0), headline_lines[0], font=fonts["headline"])[2] + 8 if headline_lines else name_x + 200
        _draw_badge(draw, badge_x, headline_y + 2, "VERBETERD", fonts)

    # --- Location ---
    location = intake.location or "Nederland"
    employer = intake.current_employer or ""
    location_text = f"{employer} | {location}" if employer else location
    location_y = headline_y + len(headline_lines[:2]) * 22 + 8
    draw.text((name_x, location_y), location_text, fill=TEXT_MUTED, font=fonts["location"])

    # --- LinkedIn buttons ---
    btn_y = location_y + 32
    # "Connectie maken" button
    _draw_rounded_rect(draw, [name_x, btn_y, name_x + 160, btn_y + 34], radius=17, fill=BTN_BLUE)
    draw.text((name_x + 20, btn_y + 8), "Connectie maken", fill=(255, 255, 255), font=fonts["btn"])

    # "Bericht" button (outlined)
    btn2_x = name_x + 172
    _draw_rounded_rect(draw, [btn2_x, btn_y, btn2_x + 100, btn_y + 34], radius=17, outline=BTN_WHITE_BORDER, width=1)
    draw.text((btn2_x + 22, btn_y + 8), "Bericht", fill=BTN_BLUE, font=fonts["btn"])

    # --- About section ---
    about_y = btn_y + 56
    draw.line([(24, about_y - 12), (MOCKUP_WIDTH - 24, about_y - 12)], fill=CARD_BORDER, width=1)
    draw.text((name_x, about_y), "Over", fill=TEXT_PRIMARY, font=fonts["section_title"])

    # "VERBETERD" badge
    about_badge_x = name_x + draw.textbbox((0, 0), "Over", font=fonts["section_title"])[2] + 10
    _draw_badge(draw, about_badge_x, about_y + 4, "VERBETERD", fonts)

    about_text = ""
    if analysis.improved_about and analysis.improved_about.full_text:
        # Strip markdown
        about_text = analysis.improved_about.full_text.replace("**", "")

    about_text_y = about_y + 32
    max_about_width = MOCKUP_WIDTH - 80 - 280  # Leave room for score card
    about_lines = _wrap_text(about_text, fonts["body"], max_about_width, draw) if about_text else ["(wordt gegenereerd)"]

    for i, line in enumerate(about_lines[:6]):
        draw.text((name_x, about_text_y + i * 20), line, fill=TEXT_SECONDARY, font=fonts["body"])

    if len(about_lines) > 6:
        more_y = about_text_y + 6 * 20
        draw.text((name_x, more_y), "...meer weergeven", fill=LINKEDIN_BLUE, font=fonts["body"])

    # --- Score card (right side) ---
    score_card_x = MOCKUP_WIDTH - 250
    score_card_y = name_y - 10
    score_card_w = 220
    score_card_h = 160

    _draw_rounded_rect(
        draw,
        [score_card_x, score_card_y, score_card_x + score_card_w, score_card_y + score_card_h],
        radius=12,
        fill=(255, 248, 243),
        outline=(255, 200, 170),
        width=1,
    )

    # Score number
    score_val = analysis.score.total_score
    score_text = str(score_val)
    score_bbox = draw.textbbox((0, 0), score_text, font=fonts["score_big"])
    score_tw = score_bbox[2] - score_bbox[0]
    draw.text(
        (score_card_x + (score_card_w - score_tw) // 2, score_card_y + 24),
        score_text,
        fill=SCORE_ORANGE,
        font=fonts["score_big"],
    )

    # "/100" label
    label_bbox = draw.textbbox((0, 0), "/100", font=fonts["score_label"])
    label_tw = label_bbox[2] - label_bbox[0]
    draw.text(
        (score_card_x + (score_card_w - label_tw) // 2, score_card_y + 68),
        "/100",
        fill=TEXT_MUTED,
        font=fonts["score_label"],
    )

    # Grade
    grade_text = f"Grade {analysis.score.grade}"
    grade_bbox = draw.textbbox((0, 0), grade_text, font=fonts["score_label"])
    grade_tw = grade_bbox[2] - grade_bbox[0]
    draw.text(
        (score_card_x + (score_card_w - grade_tw) // 2, score_card_y + 88),
        grade_text,
        fill=TEXT_SECONDARY,
        font=fonts["score_label"],
    )

    # "PROFIELSCORE" label
    ps_text = "PROFIELSCORE"
    ps_bbox = draw.textbbox((0, 0), ps_text, font=fonts["badge"])
    ps_tw = ps_bbox[2] - ps_bbox[0]
    draw.text(
        (score_card_x + (score_card_w - ps_tw) // 2, score_card_y + 120),
        ps_text,
        fill=SCORE_ORANGE,
        font=fonts["badge"],
    )

    # --- Skills section (bottom) ---
    skills_y = about_text_y + min(len(about_lines), 6) * 20 + 40
    if skills_y < MOCKUP_HEIGHT - 100:
        draw.line([(24, skills_y - 12), (MOCKUP_WIDTH - 280, skills_y - 12)], fill=CARD_BORDER, width=1)
        draw.text((name_x, skills_y), "Vaardigheden", fill=TEXT_PRIMARY, font=fonts["section_title"])

        all_skills = list(intake.current_skills.split(",")) if intake.current_skills else []
        if analysis.recommended_skills:
            all_skills.extend(analysis.recommended_skills[:5])

        skill_x = name_x
        skill_y = skills_y + 32
        for skill in all_skills[:8]:
            skill = skill.strip()
            if not skill:
                continue
            bbox = draw.textbbox((0, 0), skill, font=fonts["small"])
            sw = bbox[2] - bbox[0]
            pill_w = sw + 20

            if skill_x + pill_w > MOCKUP_WIDTH - 300:
                skill_x = name_x
                skill_y += 30

            _draw_rounded_rect(
                draw,
                [skill_x, skill_y, skill_x + pill_w, skill_y + 24],
                radius=12,
                fill=(238, 243, 248),
            )
            draw.text((skill_x + 10, skill_y + 5), skill, fill=TEXT_PRIMARY, font=fonts["small"])
            skill_x += pill_w + 8

    # Convert to PNG bytes
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", quality=95)
    return buffer.getvalue()


def build_mockup_thumbnail(analysis: ProfileAnalysis) -> bytes:
    """Generate a 600×400 email-friendly thumbnail."""
    full_bytes = build_mockup_image(analysis)

    img = Image.open(io.BytesIO(full_bytes))
    img = img.resize((600, 400), Image.LANCZOS)

    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", quality=90)
    return buffer.getvalue()


# Fix: import io at module level for build_mockup_thumbnail
import io
