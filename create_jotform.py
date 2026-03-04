"""
Script om het LinkedIn Profile Optimizer intake formulier aan te maken in JotForm.
Gebruikt de JotForm EU API.

Gebruik: python create_jotform.py
"""

import requests
import json
import os

API_KEY = os.environ.get("JOTFORM_API_TOKEN", "8446b2ba4c0c9cc79355873c4479d269")
API_BASE = os.environ.get("JOTFORM_API_BASE", "https://eu-api.jotform.com")


def create_form():
    """Maakt het LinkedIn intake formulier aan via de JotForm API."""

    # Stap 1: Maak het formulier aan
    form_data = {
        "properties[title]": "LinkedIn Profiel Optimizer — Gratis Analyse",
        "properties[height]": "600",
    }

    print("📋 Formulier aanmaken...")
    resp = requests.post(
        f"{API_BASE}/form",
        params={"apiKey": API_KEY},
        data=form_data
    )
    result = resp.json()

    if result.get("responseCode") != 200:
        print(f"❌ Fout bij aanmaken formulier: {result}")
        return

    form_id = result["content"]["id"]
    print(f"✅ Formulier aangemaakt! ID: {form_id}")

    # Stap 2: Voeg vragen toe per sectie
    questions = {}
    order = 1

    # === SECTIE 1: Over Jou ===
    questions[str(order)] = {
        "type": "control_head",
        "text": "👤 Over Jou",
        "order": str(order),
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Voornaam",
        "name": "first_name",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. Jan",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Achternaam",
        "name": "last_name",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. de Vries",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_email",
        "text": "E-mailadres",
        "name": "email",
        "order": str(order),
        "required": "Yes",
        "hint": "jouw@email.nl",
        "description": "Hier ontvang je het analyserapport",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_phone",
        "text": "Telefoonnummer",
        "name": "phone",
        "order": str(order),
        "required": "No",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Woonplaats + Provincie",
        "name": "location",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. Amsterdam, Noord-Holland",
    }
    order += 1

    # === SECTIE 2: Huidig LinkedIn Profiel ===
    questions[str(order)] = {
        "type": "control_head",
        "text": "🔗 Je Huidige LinkedIn Profiel",
        "order": str(order),
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "LinkedIn profiel URL",
        "name": "linkedin_url",
        "order": str(order),
        "required": "Yes",
        "hint": "https://linkedin.com/in/jouw-profiel",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Huidige headline / kopregel",
        "name": "current_headline",
        "order": str(order),
        "required": "Yes",
        "hint": "Kopieer je huidige LinkedIn headline hier",
        "description": "Dit is de tekst direct onder je naam op LinkedIn",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Huidige 'Over mij' / 'About' tekst",
        "name": "current_about",
        "order": str(order),
        "required": "Yes",
        "hint": "Plak hier je huidige LinkedIn 'Over mij' tekst. Als je er geen hebt, schrijf 'geen'.",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_fileupload",
        "text": "Profielfoto (upload)",
        "name": "profile_photo",
        "order": str(order),
        "required": "No",
        "description": "Optioneel: upload je huidige profielfoto zodat we die in de mockup kunnen tonen",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_radio",
        "text": "Heb je al een aangepaste LinkedIn banner?",
        "name": "has_banner",
        "order": str(order),
        "required": "Yes",
        "options": "Nee, ik heb de standaard achtergrond|Ja, maar ik wil een betere|Ja, en ik ben er tevreden mee",
    }
    order += 1

    # === SECTIE 3: Werkervaring ===
    questions[str(order)] = {
        "type": "control_head",
        "text": "💼 Werkervaring",
        "order": str(order),
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Huidige functietitel",
        "name": "current_job_title",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. Software Engineer of Projectmanager",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Huidige werkgever",
        "name": "current_employer",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. Philips of Gemeente Utrecht",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_dropdown",
        "text": "Type dienstverband",
        "name": "employment_type",
        "order": str(order),
        "required": "Yes",
        "options": "Fulltime|Parttime|ZZP / Freelance|Interim|Ondernemer / Eigenaar|Student / Starter",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_dropdown",
        "text": "Totaal jaren werkervaring",
        "name": "years_experience",
        "order": str(order),
        "required": "Yes",
        "options": "0-2 jaar|3-5 jaar|6-10 jaar|11-15 jaar|16-20 jaar|20+ jaar",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textbox",
        "text": "Startdatum huidige functie",
        "name": "current_job_start",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. mei 2022",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Beschrijving huidige functie (taken & verantwoordelijkheden)",
        "name": "current_job_description",
        "order": str(order),
        "required": "Yes",
        "hint": "Beschrijf je belangrijkste taken, verantwoordelijkheden en behaalde resultaten.",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Eerdere werkervaring (meest relevant)",
        "name": "previous_experience",
        "order": str(order),
        "required": "No",
        "hint": "Functietitel | Bedrijf | Periode | Korte beschrijving",
    }
    order += 1

    # === SECTIE 4: Doelen & Positionering ===
    questions[str(order)] = {
        "type": "control_head",
        "text": "🎯 Doelen & Positionering",
        "order": str(order),
    }
    order += 1

    questions[str(order)] = {
        "type": "control_dropdown",
        "text": "Wat is je belangrijkste doel met LinkedIn?",
        "name": "linkedin_goal",
        "order": str(order),
        "required": "Yes",
        "options": "Een nieuwe baan vinden|Meer klanten / opdrachten krijgen|Personal branding versterken|Netwerk uitbreiden in mijn sector|Zichtbaarheid als expert vergroten|Gerekruteerd worden door recruiters|Anders",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_dropdown",
        "text": "In welke sector/branche wil je actief zijn?",
        "name": "target_sector",
        "order": str(order),
        "required": "Yes",
        "options": "Bouw & Infra|Techniek & Industrie|IT & Software|Engineering & R&D|Overheid & Publieke Sector|Financiën & Banking|Logistiek & Supply Chain|Marketing & Communicatie|HR & Recruitment|Gezondheidszorg|Onderwijs|Anders",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Wie wil je bereiken op LinkedIn?",
        "name": "target_audience",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. Recruiters, HR managers, technisch directeuren",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Wat zijn je 3 belangrijkste professionele vaardigheden?",
        "name": "top_3_skills",
        "order": str(order),
        "required": "Yes",
        "hint": "1. ...\n2. ...\n3. ...",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Wat onderscheidt jou van anderen in je vakgebied?",
        "name": "unique_value",
        "order": str(order),
        "required": "Yes",
        "hint": "Jouw unieke combinatie van ervaring, kennis of aanpak",
    }
    order += 1

    # === SECTIE 5: Opleiding & Vaardigheden ===
    questions[str(order)] = {
        "type": "control_head",
        "text": "🎓 Opleiding & Vaardigheden",
        "order": str(order),
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Opleiding(en)",
        "name": "education",
        "order": str(order),
        "required": "Yes",
        "hint": "Naam opleiding | Instelling | Jaar",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Relevante certificaten",
        "name": "certificates",
        "order": str(order),
        "required": "No",
        "hint": "Bijv. PMP, Scrum Master, VCA",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_textarea",
        "text": "Vaardigheden (komma-gescheiden)",
        "name": "current_skills",
        "order": str(order),
        "required": "Yes",
        "hint": "Bijv. Python, Projectmanagement, Data-analyse, Presenteren",
    }
    order += 1

    # === SECTIE 6: Banner Voorkeuren ===
    questions[str(order)] = {
        "type": "control_head",
        "text": "🎨 Banner Voorkeuren",
        "order": str(order),
    }
    order += 1

    questions[str(order)] = {
        "type": "control_radio",
        "text": "Welke stijl banner past bij jou?",
        "name": "banner_style",
        "order": str(order),
        "required": "Yes",
        "options": "Modern & Professioneel|Tech & Innovatief|Industrieel & Robuust|Creatief & Opvallend|Minimalistisch",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_radio",
        "text": "Kleurvoorkeur voor banner",
        "name": "banner_color_preference",
        "order": str(order),
        "required": "Yes",
        "options": "Blauw (professioneel)|Donkergroen (stabiliteit)|Oranje / Amber (energie)|Donker / Antraciet (premium)|Laat de agent kiezen",
    }
    order += 1

    questions[str(order)] = {
        "type": "control_checkbox",
        "text": "Wat wil je op je banner zien?",
        "name": "banner_text_preference",
        "order": str(order),
        "required": "No",
        "options": "Mijn naam|Mijn functietitel|Mijn specialisme / tagline|Contact informatie|Geen tekst, alleen visueel",
    }
    order += 1

    # Submit button
    questions[str(order)] = {
        "type": "control_button",
        "text": "Verstuur & ontvang je gratis analyse!",
        "order": str(order),
    }

    # Stap 3: Stuur alle vragen naar de API
    print(f"📝 {order} velden toevoegen...")

    # Flatten questions for API format
    form_data = {}
    for qid, q in questions.items():
        for key, value in q.items():
            form_data[f"questions[{qid}][{key}]"] = value

    resp = requests.put(
        f"{API_BASE}/form/{form_id}/questions",
        params={"apiKey": API_KEY},
        data=form_data
    )
    result = resp.json()

    if result.get("responseCode") != 200:
        print(f"❌ Fout bij toevoegen vragen: {json.dumps(result, indent=2)}")
        return

    print(f"✅ Alle velden toegevoegd!")

    # Formulier URL
    form_url = f"https://form.jotform.com/{form_id}"
    print(f"\n{'='*60}")
    print(f"  📋 FORMULIER GEREED!")
    print(f"{'='*60}")
    print(f"  🆔 Form ID: {form_id}")
    print(f"  🔗 URL: {form_url}")
    print(f"  📝 Velden: {order}")
    print(f"\n  Volgende stap: webhook koppelen")
    print(f"  POST → https://jouw-server.com/webhook/jotform")

    return form_id


if __name__ == "__main__":
    form_id = create_form()
