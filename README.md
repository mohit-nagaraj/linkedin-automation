# linkedin-automation

Python-based LinkedIn lead finder and connector for software dev/founder personas. It:

- Logs into LinkedIn, searches people by your keywords
- Scrapes visible profile info (name, headline, location, about, top experiences, skills, followers)
- Uses Google Gemini 1.5 Flash to generate a concise profile summary and a personalized 280-char connect note
- Sends a connection request with note
- Stores leads into Google Sheets so you can review on mobile

Note: Automating LinkedIn may violate their Terms. Use responsibly and at your own risk.

## Quickstart

1) Create and activate a virtual environment

```bash
python -m venv .venv
.\\.venv\\Scripts\\activate  # Windows PowerShell
```

2) Install dependencies and Playwright browsers

```bash
pip install -U pip
pip install -r requirements.txt
python -m playwright install chromium
```

3) Configure environment variables (example `.env` snippet)

```
LINKEDIN_EMAIL=you@example.com
LINKEDIN_PASSWORD=your_password
SEARCH_KEYWORDS=software engineer, founder, cto
LOCATIONS=United States, Remote
SENIORITY_KEYWORDS=founder, cto, vp engineering, head of engineering, lead software engineer
MAX_PROFILES=25

GOOGLE_API_KEY=your_gemini_api_key

# Google Sheets (service account)
GCP_SERVICE_ACCOUNT_JSON_PATH=service_account.json
GSHEET_NAME=LinkedIn Leads
GSHEET_WORKSHEET=Leads

HEADLESS=true
SLOW_MO_MS=0
NAVIGATION_TIMEOUT_MS=30000
```

4) Run

```bash
python -m automation.orchestrator
```

## Mohit bio used for personalization

Hardcoded in `automation/orchestrator.py` as `OWNER_BIO`. Edit to your preference.

## Caution

- Respect LinkedIn’s terms and local laws. Throttle actions and add random delays if you extend this.
- UI selectors on LinkedIn change often; you may need to tweak locators in `automation/linkedin.py`.

