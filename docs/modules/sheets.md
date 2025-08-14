## Google Sheets client

File: `automation/sheets.py`

Responsibilities:
- Authenticate with Google via a service account
- Open or create the worksheet
- Append a row per processed lead

Setup:
- Create a Google Cloud service account
- Download JSON key or embed as `GCP_SERVICE_ACCOUNT_JSON`
- Share the target spreadsheet with the service account email (Editor)

Schema:
- name, headline, location, profile_url, popularity_score, summary, note, connected


