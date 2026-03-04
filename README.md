# 🚀 LinkedIn Profile Optimizer Agent v2.0

**Geautomatiseerde LinkedIn profielanalyse, optimalisatie en mockup generatie.**

Door: [Recruitin](https://recruitin.nl) — Wouter Arts

---

## Hoe werkt het?

1. **Lead vult JotForm in** → LinkedIn profiel gegevens
2. **Webhook triggert agent** → FastAPI endpoint ontvangt data
3. **Analyse engine draait** → Score, StoryBrand rewrite, SEO, verbeteringen
4. **Output gegenereerd** → Rapport + Mockup + Banner
5. **Lead ontvangt resultaat** → Email met complete analyse

## Quick Start

```bash
# 1. Installeer dependencies
pip install -r requirements.txt

# 2. Test met Victor Hendriks data
python run_analysis.py

# 3. Start webhook server
python webhook_handler.py
```

## Project Structuur

```
linkedin-optimizer-agent/
├── run_analysis.py          # 🚀 Hoofdscript — draait de volledige pipeline
├── webhook_handler.py       # 🌐 FastAPI webhook voor JotForm
├── models.py                # 📦 Pydantic data models
├── agent_config.yaml        # ⚙️ Configuratie
├── analyzer/
│   ├── profile_scorer.py    # 📊 10-criteria profiel scoring (0-100)
│   ├── storybrand_rewriter.py # 📝 StoryBrand SB7 herschrijving
│   └── seo_analyzer.py      # 🔍 SEO keyword analyse per sector
├── generator/
│   ├── mockup_builder.py    # 🖼️ HTML LinkedIn mockup generator
│   ├── banner_generator.py  # 🎨 LinkedIn banner (1584x396px)
│   ├── report_builder.py    # 📄 HTML analyse rapport
│   └── templates/
│       └── linkedin_mockup.html  # Jinja2 template
├── jotform/
│   └── linkedin_profile_intake.json  # JotForm formulier structuur
└── output/                  # Gegenereerde bestanden per lead
```

## Gebruik als Agent (via JotForm webhook)

```
POST /webhook/jotform      — JotForm submissions (Form 1 & 2)
POST /webhook/clay-callback — Clay enrichment callback
GET  /                      — Health check
```
