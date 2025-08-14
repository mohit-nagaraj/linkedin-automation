## Configuration

Use environment variables (via `.env` locally):

- LINKEDIN_EMAIL: LinkedIn username/email
- LINKEDIN_PASSWORD: LinkedIn password
- SEARCH_KEYWORDS: Comma-separated terms (e.g., "software engineer, founder, cto")
- LOCATIONS: Comma-separated locations (optional)
- SENIORITY_KEYWORDS: Comma-separated seniority signals (e.g., "founder, cto, vp engineering")
- MAX_PROFILES: Max profiles to process per run (default 25)

- GOOGLE_API_KEY: API key for Gemini 1.5 Flash

- GCP_SERVICE_ACCOUNT_JSON_PATH: Path to service account JSON for Sheets
- GCP_SERVICE_ACCOUNT_JSON: Inline JSON string (alternative to path)
- GSHEET_NAME: Target spreadsheet name
- GSHEET_WORKSHEET: Worksheet name (default "Leads")

OAuth fallback (use this if you prefer OAuth instead of a service account):
- OAUTH_CLIENT_SECRETS_PATH: Path to `credentials.json` (OAuth client)
- OAUTH_TOKEN_PATH: Path to store `token.json` (default `token.json`)

- HEADLESS: true/false for Playwright
- STORAGE_STATE_PATH: Path to save/load login cookies (default .playwright/storage_state.json)
- SLOW_MO_MS: Playwright slow motion (ms)
- NAVIGATION_TIMEOUT_MS: Navigation timeout (ms)

If both `GCP_SERVICE_ACCOUNT_JSON` and `GCP_SERVICE_ACCOUNT_JSON_PATH` are set, the inline JSON is used.


