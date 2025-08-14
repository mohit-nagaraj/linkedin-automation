# linkedin-automation

[![CI](https://img.shields.io/badge/tests-92%25%20coverage-brightgreen)](docs/testing.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Python-based LinkedIn lead finder and connector for software dev/founder personas. It:

- Logs into LinkedIn, searches people by your keywords
- Scrapes visible profile info (name, headline, location, about, top experiences, skills, followers)
- Uses Google Gemini 1.5 Flash to generate a concise profile summary and a personalized 280-char connect note
- Sends a connection request with note
- Stores leads into Google Sheets so you can review on mobile

Note: Automating LinkedIn may violate their Terms. Use responsibly and at your own risk.

## Quickstart

- Copy `.env.example` to `.env` and set `GSHEET_ID` from your sheet URL
- More config: see `docs/config.md`
- Install deps: `& ".venv\\Scripts\\pip" install -r requirements.txt`
- Run: `python main.py`
- Tests: `& ".venv\\Scripts\\python" -m pytest` (see `docs/testing.md`)

## Mohit bio used for personalization

Hardcoded in `automation/orchestrator.py` as `OWNER_BIO`. Edit to your preference.

## Caution

- Respect LinkedIn’s terms and local laws.
- UI selectors on LinkedIn change often; locators may need tweaks.

See more in `docs/`.

