"""
Banner Generator v2.0 — Expertise-Matched LinkedIn Banners
Genereert professionele LinkedIn banners (1584x396) passend bij de sector/expertise.

Twee aanpakken:
1. AI Image Generation (primair) — sector-specifieke achtergrond + Pillow text overlay
2. Pillow-only fallback — gradient + geometrie + tekst

Gebaseerd op LinkedIn banner best practices:
- Safe zone: vermijd linksonder (profielfoto overlap, vooral op mobiel)
- Tekst altijd center-rechts, boven 120px
- Semi-transparante balk achter tekst voor leesbaarheid
"""

import os
import sys
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from models import ProfileIntake

# Banner afmetingen (LinkedIn standaard 2024/2025)
BANNER_WIDTH = 1584
BANNER_HEIGHT = 396

# Safe zone: tekst begint op x=400 (rechts van profielfoto overlap)
# en eindigt 40px voor de rechterrand. Y: minimaal 30px van boven, max 280px (boven foto overlap)
SAFE_ZONE = {
    "x_start": 420,
    "x_end": BANNER_WIDTH - 60,
    "y_start": 40,
    "y_end": 280,
}

# ============================================================
# SECTOR-SPECIFIEKE AI PROMPT TEMPLATES
# ============================================================

SECTOR_PROMPTS = {
    "Bouw & Infra": (
        "Wide panoramic photograph of a modern Dutch construction site, "
        "building under construction with scaffolding, steel beams and a tower crane. "
        "Golden hour warm sunlight. Clean organized site. "
        "Blue sky with soft clouds. Elevated drone perspective. "
        "Professional construction photography, high resolution, no text, no people, no logos."
    ),
    "Techniek & Industrie": (
        "Wide panoramic photograph of a modern industrial factory interior, "
        "automated production line with robotic arms and machinery. "
        "Dramatic industrial lighting with blue and orange tones. "
        "Clean, organized manufacturing environment. "
        "Professional industrial photography, high resolution, no text, no people, no logos."
    ),
    "IT & Software": (
        "Wide panoramic photograph of abstract digital technology visualization, "
        "flowing blue and purple light streams representing data flow and neural networks. "
        "Dark background with glowing nodes and connection lines. "
        "Modern futuristic aesthetic, depth of field effect. "
        "Professional tech photography, high resolution, no text, no logos."
    ),
    "Overheid & Publieke Sector": (
        "Wide panoramic photograph of a modern Dutch government building or city hall, "
        "clean architecture with glass and concrete, green landscaping. "
        "Overcast sky, professional and authoritative atmosphere. "
        "Warm but formal lighting. "
        "Professional architectural photography, high resolution, no text, no people, no logos."
    ),
    "Engineering & R&D": (
        "Wide panoramic photograph of an engineering design studio with CAD screens "
        "and 3D printed prototypes on clean white desks. "
        "Bright, modern laboratory environment with precision instruments. "
        "Cool blue and white tones. "
        "Professional technology photography, high resolution, no text, no people, no logos."
    ),
    "HR & Recruitment": (
        "Wide panoramic photograph of a modern bright office space "
        "with open collaboration areas, warm lighting, plants and natural elements. "
        "Inviting and professional corporate environment. "
        "Warm golden tones, clean aesthetic. "
        "Professional corporate photography, high resolution, no text, no people, no logos."
    ),
    "Logistiek & Supply Chain": (
        "Wide panoramic photograph of a modern automated warehouse "
        "with conveyor belts, organized inventory shelving, and loading docks. "
        "Clean, efficient logistics environment. "
        "Professional warehousing photography, high resolution, no text, no people, no logos."
    ),
    "Financiën & Banking": (
        "Wide panoramic photograph of a modern financial district skyline "
        "with glass office towers reflecting sunset light. "
        "Clean urban landscape, professional and premium atmosphere. "
        "Professional cityscape photography, high resolution, no text, no logos."
    ),
    "Marketing & Communicatie": (
        "Wide panoramic photograph of a modern creative agency workspace "
        "with colorful mood boards, large displays showing campaign visuals. "
        "Bright, inspiring creative environment with warm lighting. "
        "Professional interior photography, high resolution, no text, no people, no logos."
    ),
    "Gezondheidszorg": (
        "Wide panoramic photograph of a modern hospital or healthcare facility, "
        "clean corridors with natural light, medical equipment visible. "
        "Calm, professional healthcare environment in white and soft blue tones. "
        "Professional medical photography, high resolution, no text, no people, no logos."
    ),
    "Onderwijs": (
        "Wide panoramic photograph of a modern university campus or lecture hall, "
        "bright open spaces with bookshelves and natural light. "
        "Academic and inviting atmosphere. "
        "Professional campus photography, high resolution, no text, no people, no logos."
    ),
}

# Fallback prompt als sector niet gevonden wordt
DEFAULT_PROMPT = (
    "Wide panoramic photograph of a modern professional office environment, "
    "clean architecture with glass walls and natural light. "
    "Professional corporate photography, high resolution, no text, no people, no logos."
)

# ============================================================
# KLEURENPALET PER SECTOR (voor tekst overlay)
# ============================================================

SECTOR_COLORS = {
    "Bouw & Infra": {"overlay": (30, 58, 47, 180), "text": (255, 255, 255), "accent": (251, 191, 36)},
    "Techniek & Industrie": {"overlay": (17, 24, 39, 180), "text": (255, 255, 255), "accent": (96, 165, 250)},
    "IT & Software": {"overlay": (49, 10, 101, 180), "text": (255, 255, 255), "accent": (167, 139, 250)},
    "Overheid & Publieke Sector": {"overlay": (6, 78, 59, 180), "text": (255, 255, 255), "accent": (110, 231, 183)},
    "Engineering & R&D": {"overlay": (31, 41, 55, 180), "text": (255, 255, 255), "accent": (156, 163, 175)},
    "HR & Recruitment": {"overlay": (10, 102, 194, 180), "text": (255, 255, 255), "accent": (253, 224, 71)},
    "Logistiek & Supply Chain": {"overlay": (120, 53, 15, 180), "text": (255, 255, 255), "accent": (253, 186, 116)},
    "Financiën & Banking": {"overlay": (17, 24, 39, 190), "text": (255, 255, 255), "accent": (96, 165, 250)},
    "Marketing & Communicatie": {"overlay": (157, 23, 77, 180), "text": (255, 255, 255), "accent": (251, 207, 232)},
    "Gezondheidszorg": {"overlay": (3, 105, 161, 180), "text": (255, 255, 255), "accent": (186, 230, 253)},
    "Onderwijs": {"overlay": (30, 64, 175, 180), "text": (255, 255, 255), "accent": (191, 219, 254)},
}

DEFAULT_COLORS = {"overlay": (31, 41, 55, 180), "text": (255, 255, 255), "accent": (156, 163, 175)}


# ============================================================
# PUBLIC API
# ============================================================

def generate_banner_prompt(intake: ProfileIntake) -> str:
    """
    Genereert de AI prompt voor het maken van een sector-specifieke
    LinkedIn banner achtergrond. Te gebruiken met image generation tools.
    """
    sector = intake.target_sector
    base_prompt = _get_sector_prompt(sector)
    return f"{base_prompt} Aspect ratio must be exactly 4:1 (very wide, short). Dimensions: 1584x396 pixels."


def generate_banner_from_image(
    background_path: str,
    intake: ProfileIntake,
    output_dir: str = "./output"
) -> str:
    """
    Neemt een AI-gegenereerde achtergrondafbeelding en voegt
    een professionele tekst overlay toe in de safe zone.

    Args:
        background_path: Pad naar de AI-gegenereerde achtergrondafbeelding
        intake: ProfileIntake met naam, functie, sector etc.
        output_dir: Output directory

    Returns:
        Pad naar de finale banner PNG
    """
    os.makedirs(output_dir, exist_ok=True)

    # Open en resize achtergrond naar exact 1584x396
    bg = Image.open(background_path).convert("RGBA")
    bg = _resize_and_crop(bg, BANNER_WIDTH, BANNER_HEIGHT)

    # Maak overlay layer
    overlay = Image.new("RGBA", (BANNER_WIDTH, BANNER_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Haal sector kleuren op
    colors = _get_sector_colors(intake.target_sector)

    # Teken semi-transparante balk in safe zone (rechterhelft)
    bar_x = SAFE_ZONE["x_start"] - 30
    bar_y = SAFE_ZONE["y_start"] - 10
    bar_w = SAFE_ZONE["x_end"] + 30
    bar_h = SAFE_ZONE["y_end"] + 20
    _draw_rounded_rect(draw, bar_x, bar_y, bar_w, bar_h, radius=16, fill=colors["overlay"])

    # Teken accent lijn links van de tekst
    accent_x = SAFE_ZONE["x_start"] - 10
    draw.line(
        [(accent_x, SAFE_ZONE["y_start"] + 10), (accent_x, SAFE_ZONE["y_end"] - 10)],
        fill=colors["accent"], width=4
    )

    # Laad fonts
    fonts = _load_fonts()

    # Teken tekst in safe zone
    text_x = SAFE_ZONE["x_start"] + 10
    text_y = SAFE_ZONE["y_start"] + 15

    # Naam
    draw.text((text_x, text_y), intake.full_name, fill=colors["text"], font=fonts["name"])
    text_y += 50

    # Functietitel
    draw.text((text_x, text_y), intake.current_job_title, fill=colors["text"], font=fonts["title"])
    text_y += 35

    # Separator lijn
    draw.line(
        [(text_x, text_y + 5), (text_x + 300, text_y + 5)],
        fill=(*colors["accent"][:3], 150), width=2
    )
    text_y += 20

    # Specialisme / top skill
    tagline = _get_tagline(intake)
    draw.text((text_x, text_y), tagline, fill=(*colors["text"][:3], 220), font=fonts["tagline"])
    text_y += 30

    # Locatie
    location_text = f"📍 {intake.location}"
    draw.text((text_x, text_y), location_text, fill=(*colors["text"][:3], 180), font=fonts["small"])

    # Combineer achtergrond + overlay
    result = Image.alpha_composite(bg, overlay)

    # Subtiele Recruitin branding rechtsonder
    _draw_branding(ImageDraw.Draw(result), colors)

    # Converteer naar RGB en sla op
    result = result.convert("RGB")
    safe_name = intake.full_name.replace(" ", "_")
    output_path = os.path.join(output_dir, f"{safe_name}_LinkedIn_Banner.png")
    result.save(output_path, "PNG", quality=95)

    print(f"✅ Banner gegenereerd: {output_path}")
    return output_path


def generate_banner_pillow_only(intake: ProfileIntake, output_dir: str = "./output") -> str:
    """
    Pillow-only fallback: genereert een professionele banner
    zonder AI achtergrondafbeelding.
    """
    os.makedirs(output_dir, exist_ok=True)

    img = Image.new("RGBA", (BANNER_WIDTH, BANNER_HEIGHT))
    draw = ImageDraw.Draw(img)

    colors = _get_sector_colors(intake.target_sector)

    # Gradient achtergrond
    overlay_rgb = colors["overlay"][:3]
    darker = tuple(max(0, c - 40) for c in overlay_rgb)
    _draw_gradient(draw, overlay_rgb, darker)

    # Subtiele geometrische elementen
    _draw_geometric_elements(draw, colors["accent"], intake.target_sector)

    # Tekst overlay (zelfde logica als generate_banner_from_image)
    fonts = _load_fonts()
    text_x = SAFE_ZONE["x_start"] + 10
    text_y = SAFE_ZONE["y_start"] + 15

    draw.text((text_x, text_y), intake.full_name, fill=colors["text"], font=fonts["name"])
    text_y += 50
    draw.text((text_x, text_y), intake.current_job_title, fill=colors["text"], font=fonts["title"])
    text_y += 35
    draw.line(
        [(text_x, text_y + 5), (text_x + 300, text_y + 5)],
        fill=colors["accent"], width=2
    )
    text_y += 20
    tagline = _get_tagline(intake)
    draw.text((text_x, text_y), tagline, fill=(*colors["text"][:3], 220), font=fonts["tagline"])
    text_y += 30
    draw.text((text_x, text_y), f"📍 {intake.location}",
              fill=(*colors["text"][:3], 180), font=fonts["small"])

    _draw_branding(draw, colors)

    result = img.convert("RGB")
    safe_name = intake.full_name.replace(" ", "_")
    output_path = os.path.join(output_dir, f"{safe_name}_LinkedIn_Banner.png")
    result.save(output_path, "PNG", quality=95)

    print(f"✅ Banner (Pillow fallback) gegenereerd: {output_path}")
    return output_path


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_sector_prompt(sector: str) -> str:
    """Zoekt de sector-specifieke AI prompt op."""
    for key, prompt in SECTOR_PROMPTS.items():
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            return prompt
    return DEFAULT_PROMPT


def _get_sector_colors(sector: str) -> dict:
    """Zoekt sector-specifieke kleuren op."""
    for key, colors in SECTOR_COLORS.items():
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            return colors
    return DEFAULT_COLORS


def _resize_and_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Resize en crop een afbeelding naar exact target_w × target_h.
    Behoudt de center crop voor het beste resultaat.
    """
    # Bereken de benodigde schaal
    src_ratio = img.width / img.height
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # Bron is breder → schaal op hoogte, crop breedte
        new_h = target_h
        new_w = int(img.width * (target_h / img.height))
    else:
        # Bron is hoger → schaal op breedte, crop hoogte
        new_w = target_w
        new_h = int(img.height * (target_w / img.width))

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    return img


def _draw_rounded_rect(draw, x1, y1, x2, y2, radius, fill):
    """Tekent een rechthoek met afgeronde hoeken."""
    # Maak een RGB fill als er een alpha is
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)


def _load_fonts() -> dict:
    """Laadt systeemfonts, met fallback naar defaults."""
    fonts = {}
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFPro.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]

    font_file = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_file = fp
            break

    if font_file:
        fonts["name"] = ImageFont.truetype(font_file, 40)
        fonts["title"] = ImageFont.truetype(font_file, 24)
        fonts["tagline"] = ImageFont.truetype(font_file, 20)
        fonts["small"] = ImageFont.truetype(font_file, 16)
        fonts["tiny"] = ImageFont.truetype(font_file, 12)
    else:
        default = ImageFont.load_default()
        fonts = {k: default for k in ["name", "title", "tagline", "small", "tiny"]}

    return fonts


def _get_tagline(intake: ProfileIntake) -> str:
    """Genereert een korte tagline op basis van expertise."""
    skills = intake.top_3_skills.strip()
    if skills:
        first_skill = skills.split("\n")[0].strip()
        if len(first_skill) <= 60:
            return first_skill
    if intake.unique_value:
        first_sentence = intake.unique_value.split(".")[0].strip()
        if len(first_sentence) <= 60:
            return first_sentence
    return intake.target_sector


def _draw_gradient(draw, start_color, end_color):
    """Tekent een diagonale gradient."""
    for x in range(BANNER_WIDTH):
        for y in range(BANNER_HEIGHT):
            ratio = (x / BANNER_WIDTH * 0.7) + (y / BANNER_HEIGHT * 0.3)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            draw.point((x, y), fill=(r, g, b))


def _draw_geometric_elements(draw, accent, sector):
    """Tekent subtiele geometrische elementen per sector (voor Pillow fallback)."""
    accent_faded = (*accent[:3], 40)

    # Subtiele diagonale lijnen in de linkerhelft (achtergrond detail)
    for i in range(-BANNER_HEIGHT, 400, 50):
        draw.line(
            [(i, 0), (i + BANNER_HEIGHT, BANNER_HEIGHT)],
            fill=accent_faded, width=1
        )

    # Cirkel accent linksonder
    draw.ellipse(
        [-50, BANNER_HEIGHT - 150, 200, BANNER_HEIGHT + 50],
        outline=(*accent[:3], 30), width=2
    )

    # Accent lijn onderaan
    draw.line(
        [(0, BANNER_HEIGHT - 3), (350, BANNER_HEIGHT - 3)],
        fill=accent, width=3
    )


def _draw_branding(draw, colors):
    """Subtiele Recruitin branding rechtsonder."""
    fonts = _load_fonts()
    text = "Optimized by Recruitin.nl"
    faded_color = (*colors["text"][:3], 100)
    draw.text(
        (BANNER_WIDTH - 210, BANNER_HEIGHT - 25),
        text, fill=faded_color, font=fonts["tiny"]
    )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Gebruik: python banner_generator.py <intake.json>")
        print("Genereert een Pillow-fallback banner. Gebruik generate_banner_from_image() voor AI banner.")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    test = ProfileIntake(**data)

    print(f"\n📝 AI Banner Prompt:\n{generate_banner_prompt(test)}\n")

    path = generate_banner_pillow_only(test, output_dir="/tmp/banner_test")
    print(f"Pillow fallback: {path}")
