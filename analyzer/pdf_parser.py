"""
LinkedIn PDF Parser — extracts profile data from LinkedIn's "Save as PDF" export.

LinkedIn PDFs have a 2-column layout:
- LEFT sidebar: Contact info, Top Skills, Languages, Honors
- RIGHT main: Name, Headline, Summary, Experience, Education

We use pdfplumber's word-level extraction to separate columns by x-position,
then parse the main column content.
"""

import re
from dataclasses import dataclass, field


@dataclass
class LinkedInPDFData:
    full_name: str = ""
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    experiences: list = field(default_factory=list)
    education: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    certificates: list = field(default_factory=list)
    languages: list = field(default_factory=list)


# Section headers in both EN and NL
SECTION_HEADERS = {
    "experience": ["Experience", "Ervaring", "Werkervaring"],
    "education": ["Education", "Opleiding", "Opleidingen"],
    "skills": ["Skills", "Vaardigheden", "Top Skills", "Top vaardigheden"],
    "about": ["Summary", "About", "Over", "Samenvatting"],
    "certifications": ["Certifications", "Certificeringen", "Licenses & Certifications",
                        "Licenties en certificeringen", "Licenties & certificeringen"],
    "languages": ["Languages", "Talen"],
    "honors": ["Honors & Awards", "Onderscheidingen", "Honors-Awards"],
    "volunteer": ["Volunteer Experience", "Vrijwilligerswerk"],
    "projects": ["Projects", "Projecten"],
    "publications": ["Publications", "Publicaties"],
    "recommendations": ["Recommendations", "Aanbevelingen"],
}

# All headers flattened
ALL_HEADERS = []
for headers in SECTION_HEADERS.values():
    ALL_HEADERS.extend(headers)

# Sidebar headers (left column) — these should not appear in main content
SIDEBAR_HEADERS = ["Contact", "Top Skills", "Top vaardigheden", "Languages", "Talen",
                    "Honors-Awards", "Honors & Awards", "Onderscheidingen",
                    "Certifications", "Certificeringen"]


def parse_linkedin_pdf(pdf_bytes: bytes) -> LinkedInPDFData:
    """Parse a LinkedIn PDF export and extract structured profile data."""
    import pdfplumber
    import io

    result = LinkedInPDFData()

    try:
        pdf = pdfplumber.open(io.BytesIO(pdf_bytes))
    except Exception as e:
        print(f"   ⚠️ PDF parsing error: {e}")
        return result

    # Strategy: extract words with positions, split into left/right columns
    main_lines = []
    sidebar_lines = []

    for page in pdf.pages:
        page_width = page.width
        # Column boundary: ~35% of page width (sidebar is narrow)
        col_boundary = page_width * 0.35

        words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
        if not words:
            continue

        # Group words by their y-position (same line)
        lines_by_y = {}
        for w in words:
            # Round y to group words on same line
            y_key = round(w["top"] / 4) * 4
            if y_key not in lines_by_y:
                lines_by_y[y_key] = {"left": [], "right": []}
            if w["x0"] < col_boundary:
                lines_by_y[y_key]["left"].append(w)
            else:
                lines_by_y[y_key]["right"].append(w)

        # Sort by y position and build text
        for y_key in sorted(lines_by_y.keys()):
            groups = lines_by_y[y_key]
            if groups["right"]:
                right_words = sorted(groups["right"], key=lambda w: w["x0"])
                line_text = " ".join(w["text"] for w in right_words).strip()
                if line_text and not _is_page_marker(line_text):
                    main_lines.append(line_text)
            if groups["left"]:
                left_words = sorted(groups["left"], key=lambda w: w["x0"])
                line_text = " ".join(w["text"] for w in left_words).strip()
                if line_text and not _is_page_marker(line_text):
                    sidebar_lines.append(line_text)

    pdf.close()

    if not main_lines:
        return result

    # Parse sidebar for skills, languages, contact info
    _parse_sidebar(sidebar_lines, result)

    # Parse main column
    _parse_main_column(main_lines, result)

    return result


def _is_page_marker(line: str) -> bool:
    """Check if line is a page number/marker."""
    return bool(re.match(r"^Page \d+ of \d+$", line))


def _parse_sidebar(lines: list, result: LinkedInPDFData):
    """Parse the left sidebar for skills, languages, etc."""
    current_section = None

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        # Check for sidebar section headers
        lower = clean.lower()
        if lower == "contact":
            current_section = "contact"
            continue
        elif lower in ("top skills", "top vaardigheden"):
            current_section = "skills"
            continue
        elif lower in ("languages", "talen"):
            current_section = "languages"
            continue
        elif lower in ("honors-awards", "honors & awards", "onderscheidingen"):
            current_section = "honors"
            continue
        elif lower in ("certifications", "certificeringen"):
            current_section = "certifications"
            continue

        # Collect items
        if current_section == "skills":
            result.skills.append(clean)
        elif current_section == "languages":
            result.languages.append(clean)
        elif current_section == "certifications":
            result.certificates.append(clean)


def _parse_main_column(lines: list, result: LinkedInPDFData):
    """Parse the main (right) column for name, headline, summary, experience, education."""
    if not lines:
        return

    # First line is typically the name
    result.full_name = lines[0].strip()
    if result.full_name:
        parts = result.full_name.split(" ", 1)
        result.first_name = parts[0]
        result.last_name = parts[1] if len(parts) > 1 else ""

    # Lines before first section header = header area (headline, location)
    # Find first section header
    first_section_idx = len(lines)
    for i, line in enumerate(lines[1:], 1):
        if _is_section_header(line):
            first_section_idx = i
            break

    # Header lines (between name and first section)
    header_lines = lines[1:first_section_idx]

    # Headline is typically the first meaningful line after name
    headline_parts = []
    for line in header_lines:
        if _looks_like_location(line):
            result.location = line
        elif re.match(r"^www\.|^http", line, re.IGNORECASE):
            continue  # Skip URL lines
        elif re.match(r"^[\w.]+@[\w.]+", line):
            continue  # Skip email lines
        elif re.match(r"^\d{2,3}[-\s]", line):
            continue  # Skip phone numbers
        elif not result.headline:
            # Collect headline (may span multiple lines)
            headline_parts.append(line)
        elif headline_parts and not result.location and not _looks_like_location(line):
            headline_parts.append(line)

    if headline_parts:
        result.headline = " ".join(headline_parts)

    # Now split remaining lines into sections
    sections = _split_into_sections(lines[first_section_idx:])

    # About/Summary
    for key in SECTION_HEADERS["about"]:
        section = _find_section(sections, key)
        if section is not None:
            result.about = "\n".join(section)
            break

    # Experience
    for key in SECTION_HEADERS["experience"]:
        section = _find_section(sections, key)
        if section is not None:
            result.experiences = _parse_experience_section(section)
            break

    # Education
    for key in SECTION_HEADERS["education"]:
        section = _find_section(sections, key)
        if section is not None:
            result.education = _parse_education_section(section)
            break


def _is_section_header(line: str) -> bool:
    """Check if a line is a known section header."""
    clean = line.strip()
    for header in ALL_HEADERS:
        if clean.lower() == header.lower():
            return True
    return False


def _find_section(sections: dict, key: str):
    """Find a section by case-insensitive key match."""
    for k in sections:
        if k.lower() == key.lower():
            return sections[k]
    return None


def _split_into_sections(lines: list) -> dict:
    """Split lines into named sections based on known headers."""
    sections = {}
    current_section = None

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        if _is_section_header(clean):
            current_section = clean
            sections[current_section] = []
        elif current_section is not None:
            sections[current_section].append(clean)

    return sections


def _looks_like_location(line: str) -> bool:
    """Heuristic: does this line look like a location?"""
    location_indicators = [
        "Nederland", "Netherlands", "Belgium", "België", "Germany", "Deutschland",
        "Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Eindhoven", "Groningen",
        "Area", "Regio", "Metropolitan", "Province", "Provincie", "Gelderland",
        "Noord-Holland", "Zuid-Holland", "Noord-Brabant", "Limburg", "Overijssel",
    ]
    for indicator in location_indicators:
        if indicator.lower() in line.lower():
            return True
    # Pattern: "City, Country" or "City, Province, Country"
    if re.match(r"^[A-Z][a-z]+,\s+[A-Z]", line):
        return True
    return False


def _parse_experience_section(lines: list) -> list:
    """Parse experience lines into structured entries.

    LinkedIn PDF experience format (per entry):
      Company Name
      Job Title
      Date Range (e.g. "March 2012 - Present (14 years 2 months)")
      Location (optional)
      Description lines...
    """
    entries = []
    current_entry = None
    date_pattern = re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December|"
        r"jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)?\s*\d{4}\s*[-–]\s*"
        r"(Present|Heden|heden|present|"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)?\s*\d{4})",
        re.IGNORECASE
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look ahead: if next line or line after is a date, this is a company name
        if i + 1 < len(lines) and date_pattern.search(lines[i + 1]):
            # This line = company, next = dates (no separate title line)
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "company": line,
                "title": "",
                "dates": lines[i + 1],
                "description": ""
            }
            i += 2
            continue

        if i + 2 < len(lines) and date_pattern.search(lines[i + 2]):
            # This line = company, next = title, line after = dates
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "company": line,
                "title": lines[i + 1],
                "dates": lines[i + 2],
                "description": ""
            }
            i += 3
            continue

        # If we're inside an entry, append to description
        if current_entry:
            if current_entry["description"]:
                current_entry["description"] += " " + line
            else:
                current_entry["description"] = line
        i += 1

    if current_entry:
        entries.append(current_entry)

    return entries


def _parse_education_section(lines: list) -> list:
    """Parse education lines into structured entries."""
    entries = []
    current = []

    for line in lines:
        # New education entry often starts with institution name
        # Date pattern in education: "(1996 - 2000)" or "1996 - 2000"
        if current and not re.search(r"\d{4}", line) and len(line) > 5:
            # Looks like a new institution name
            if len(current) > 1 or (current and re.search(r"\d{4}", current[0])):
                entries.append(" | ".join(current))
                current = [line]
                continue
        current.append(line)

    if current:
        entries.append(" | ".join(current))

    return entries


def pdf_data_to_intake_fields(pdf_data: LinkedInPDFData) -> dict:
    """Convert parsed PDF data into fields compatible with ProfileIntake constructor."""
    # Format experience as text
    exp_parts = []
    for exp in pdf_data.experiences[:5]:  # Max 5 recent
        parts = []
        if exp.get("title"):
            parts.append(exp["title"])
        if exp.get("company"):
            parts.append(f"bij {exp['company']}")
        if exp.get("dates"):
            parts.append(f"({exp['dates']})")
        if exp.get("description"):
            parts.append(f"— {exp['description'][:200]}")
        if parts:
            exp_parts.append(" ".join(parts))

    # Estimate years of experience from dates
    years_exp = _estimate_years_experience(pdf_data.experiences)

    # Current job = first experience entry
    current_title = ""
    current_employer = ""
    current_description = ""
    if pdf_data.experiences:
        first = pdf_data.experiences[0]
        current_title = first.get("title", "")
        current_employer = first.get("company", "")
        current_description = first.get("description", "")

    return {
        "first_name": pdf_data.first_name,
        "last_name": pdf_data.last_name,
        "current_headline": pdf_data.headline,
        "current_about": pdf_data.about or "geen",
        "location": pdf_data.location,
        "current_job_title": current_title,
        "current_employer": current_employer,
        "current_job_description": current_description,
        "previous_experience": "\n".join(exp_parts[1:]) if len(exp_parts) > 1 else "",
        "years_experience": years_exp,
        "education": " | ".join(pdf_data.education) if pdf_data.education else "",
        "certificates": ", ".join(pdf_data.certificates) if pdf_data.certificates else "",
        "current_skills": ", ".join(pdf_data.skills) if pdf_data.skills else "",
    }


def detect_sector_from_profile(pdf_data: LinkedInPDFData) -> str:
    """Auto-detect target sector from profile text (headline + about + experience)."""
    all_text = " ".join([
        pdf_data.headline,
        pdf_data.about,
        " ".join(s for s in pdf_data.skills),
        " ".join(exp.get("title", "") + " " + exp.get("company", "") + " " + exp.get("description", "")
                 for exp in pdf_data.experiences[:3])
    ]).lower()

    sector_signals = {
        "HR & Recruitment": ["recruit", "hr ", "human resource", "talent", "werving", "selectie",
                              "sourcing", "employer brand", "rpo", "staffing", "uitzend"],
        "IT & Software": ["software", "developer", "programmeur", "devops", "cloud", "saas",
                           "data engineer", "frontend", "backend", "full stack", "agile", "scrum"],
        "Bouw & Constructie": ["bouw", "constructie", "aannemer", "uitvoerder", "werkvoorbereider",
                                "civiel", "infra", "wegen", "heijmans", "bam", "volker"],
        "Techniek & Productie": ["technisch", "productie", "manufacturing", "cnc", "engineer",
                                  "onderhoud", "mechatronica", "elektro", "installatie"],
        "Olie & Gas": ["oil", "gas", "offshore", "petrochemie", "refinery", "pipeline"],
        "Overheid & Publiek": ["gemeente", "overheid", "toezicht", "vergunning", "handhaving",
                                "rijkswaterstaat", "provincie"],
        "Finance & Consulting": ["finance", "consulting", "advisory", "accountant", "audit",
                                  "controller", "cfo", "financieel"],
        "Sales & Marketing": ["sales", "marketing", "business development", "account manager",
                               "commercieel", "acquisitie"],
    }

    best_sector = ""
    best_count = 0
    for sector, keywords in sector_signals.items():
        count = sum(1 for kw in keywords if kw in all_text)
        if count > best_count:
            best_count = count
            best_sector = sector

    return best_sector or "Overig"


def detect_goal_from_profile(pdf_data: LinkedInPDFData) -> str:
    """Auto-detect linkedin goal from profile context."""
    headline = pdf_data.headline.lower()
    about = pdf_data.about.lower()

    # Business owner signals
    owner_signals = ["directeur", "eigenaar", "founder", "oprichter", "ceo", "managing",
                      "ondernemer", "zelfstandig", "freelance", "zzp"]
    if any(s in headline for s in owner_signals):
        return "Meer klanten / opdrachten krijgen"

    # Job seeker signals
    seeker_signals = ["open voor", "beschikbaar", "zoek", "looking for", "seeking"]
    if any(s in headline or s in about for s in seeker_signals):
        return "Een nieuwe baan vinden"

    return "Mijn personal brand versterken"


def detect_audience_from_profile(pdf_data: LinkedInPDFData, sector: str) -> str:
    """Auto-detect target audience based on sector and role."""
    headline = pdf_data.headline.lower()

    if "recruit" in headline or "hr" in headline:
        return "Technisch directeuren, HR managers en operationeel leidinggevenden bij technische MKB bedrijven (50-800 medewerkers)"
    elif "directeur" in headline or "eigenaar" in headline:
        return "Potentiële klanten, partners en talent in de sector"
    elif "sales" in headline or "commerci" in headline:
        return "Decision makers en inkopers bij doelbedrijven"
    else:
        return f"Recruiters, hiring managers en professionals in {sector}"


def _estimate_years_experience(experiences: list) -> str:
    """Estimate total years from experience date ranges."""
    if not experiences:
        return ""
    years = set()
    for exp in experiences:
        dates = exp.get("dates", "")
        found = re.findall(r"(\d{4})", dates)
        for y in found:
            years.add(int(y))
    if years:
        span = max(years) - min(years)
        if span <= 2:
            return "0-2 jaar"
        elif span <= 5:
            return "3-5 jaar"
        elif span <= 10:
            return "6-10 jaar"
        else:
            return "10+ jaar"
    return ""
