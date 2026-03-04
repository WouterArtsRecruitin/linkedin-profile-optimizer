"""
LinkedIn Profile Optimizer Agent — Data Models
Pydantic models voor profiel intake, analyse en output.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime


# ============================================================
# ENUMS
# ============================================================

class LinkedInGoal(str, Enum):
    NEW_JOB = "Een nieuwe baan vinden"
    MORE_CLIENTS = "Meer klanten / opdrachten krijgen"
    PERSONAL_BRANDING = "Personal branding versterken"
    NETWORK = "Netwerk uitbreiden in mijn sector"
    EXPERT_VISIBILITY = "Zichtbaarheid als expert vergroten"
    GET_RECRUITED = "Gerekruteerd worden door recruiters"
    OTHER = "Anders"


class TargetSector(str, Enum):
    CONSTRUCTION = "Bouw & Infra"
    TECH_INDUSTRY = "Techniek & Industrie"
    IT_SOFTWARE = "IT & Software"
    ENGINEERING = "Engineering & R&D"
    GOVERNMENT = "Overheid & Publieke Sector"
    FINANCE = "Financiën & Banking"
    LOGISTICS = "Logistiek & Supply Chain"
    MARKETING = "Marketing & Communicatie"
    HR_RECRUITMENT = "HR & Recruitment"
    HEALTHCARE = "Gezondheidszorg"
    EDUCATION = "Onderwijs"
    OTHER = "Anders"


class BannerStyle(str, Enum):
    MODERN_PROFESSIONAL = "Modern & Professioneel"
    TECH_INNOVATIVE = "Tech & Innovatief"
    INDUSTRIAL_ROBUST = "Industrieel & Robuust"
    CREATIVE_BOLD = "Creatief & Opvallend"
    MINIMALIST = "Minimalistisch"


class BannerColor(str, Enum):
    BLUE = "Blauw"
    DARK_GREEN = "Donkergroen"
    ORANGE_AMBER = "Oranje/Amber"
    DARK_ANTHRACITE = "Donker/Antraciet"
    AUTO = "Laat de agent kiezen"


# ============================================================
# INPUT MODELS (van JotForm)
# ============================================================

class ProfileIntake(BaseModel):
    """Alle gegevens die de gebruiker via JotForm invoert."""

    # Sectie 1: Persoonlijke gegevens
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    location: str

    # Sectie 2: Huidig LinkedIn profiel
    linkedin_url: str
    current_headline: str
    current_about: str
    profile_photo_url: Optional[str] = None
    has_banner: str = "Nee, ik heb de standaard achtergrond"

    # Sectie 3: Werkervaring
    current_job_title: str
    current_employer: str
    employment_type: str = "Fulltime"
    years_experience: str = "6-10 jaar"
    current_job_start: str = ""
    current_job_description: str = ""
    previous_experience: Optional[str] = None

    # Sectie 4: Doelen & Positionering
    linkedin_goal: str = LinkedInGoal.NEW_JOB
    target_sector: str = TargetSector.CONSTRUCTION
    target_audience: str = ""
    top_3_skills: str = ""
    unique_value: str = ""

    # Sectie 5: Opleiding & Vaardigheden
    education: str = ""
    certificates: Optional[str] = None
    current_skills: str = ""

    # Sectie 6: Banner voorkeuren
    banner_style: str = BannerStyle.MODERN_PROFESSIONAL
    banner_color_preference: str = BannerColor.AUTO
    banner_text_preference: Optional[List[str]] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def parse_skills_list(self) -> List[str]:
        """Parse komma-gescheiden skills naar een lijst."""
        if not self.current_skills:
            return []
        return [s.strip() for s in self.current_skills.split(",") if s.strip()]

    def parse_education_items(self) -> List[dict]:
        """Parse opleiding tekst naar gestructureerde items."""
        items = []
        if not self.education:
            return items
        for line in self.education.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            item = {"degree": parts[0]}
            if len(parts) > 1:
                item["school"] = parts[1]
            if len(parts) > 2:
                item["year"] = parts[2]
            items.append(item)
        return items

    def parse_experience_items(self) -> List[dict]:
        """Parse eerdere werkervaring tekst naar gestructureerde items."""
        items = []
        if not self.previous_experience:
            return items
        for line in self.previous_experience.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            item = {"title": parts[0]}
            if len(parts) > 1:
                item["company"] = parts[1]
            if len(parts) > 2:
                item["period"] = parts[2]
            if len(parts) > 3:
                item["description"] = parts[3]
            items.append(item)
        return items


# ============================================================
# SCORING MODELS
# ============================================================

class ScoreCategory(BaseModel):
    """Score voor een individuele categorie."""
    name: str
    score: int = Field(ge=0, le=10)
    max_score: int = 10
    weight_pct: int
    feedback: str = ""
    suggestions: List[str] = []


class ProfileScore(BaseModel):
    """Volledige profielscore met breakdown."""
    total_score: int = Field(ge=0, le=100)
    grade: str = ""  # A, B, C, D, F
    categories: List[ScoreCategory] = []
    summary: str = ""
    top_improvements: List[str] = []

    def calculate_grade(self) -> str:
        if self.total_score >= 85:
            return "A"
        elif self.total_score >= 70:
            return "B"
        elif self.total_score >= 55:
            return "C"
        elif self.total_score >= 40:
            return "D"
        else:
            return "F"


# ============================================================
# OUTPUT MODELS
# ============================================================

class HeadlineOption(BaseModel):
    """Een headline optie met toelichting."""
    style: str  # "Direct", "Resultaatgericht", "Autoriteit"
    text: str
    explanation: str


class ImprovedAbout(BaseModel):
    """Verbeterde 'Over mij' tekst met StoryBrand structuur."""
    full_text: str
    word_count: int = 0
    sections: dict = {}  # StoryBrand secties (problem, guide, plan, result, cta)


class SEOKeyword(BaseModel):
    """Een aanbevolen SEO keyword."""
    keyword: str
    relevance_score: int = Field(ge=1, le=10)
    reason: str
    where_to_add: str  # "headline", "about", "skills", "experience"


class ImprovedExperience(BaseModel):
    """Verbeterde werkervaring beschrijving."""
    company: str
    title: str
    period: str
    original_description: str
    improved_description: str
    key_improvements: List[str] = []


class ProfileAnalysis(BaseModel):
    """Complete analyse output — het hoofdresultaat van de agent."""
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    intake: ProfileIntake

    # Score
    score: ProfileScore

    # Verbeteringen
    headline_options: List[HeadlineOption] = []
    improved_about: Optional[ImprovedAbout] = None
    seo_keywords: List[SEOKeyword] = []
    improved_experiences: List[ImprovedExperience] = []
    recommended_skills: List[str] = []

    # Banner
    banner_prompt: str = ""  # AI prompt voor banner generatie

    # Concrete actiepunten
    action_items: List[str] = []

    # Verwachte resultaten
    expected_results: dict = {}

    # Output paden
    mockup_html_path: Optional[str] = None
    mockup_png_path: Optional[str] = None
    report_pdf_path: Optional[str] = None
    banner_png_path: Optional[str] = None
