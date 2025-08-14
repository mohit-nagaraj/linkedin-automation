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
- GSHEET_ID: Spreadsheet ID (preferred). Copy from the sheet URL segment between `/d/` and `/edit`.
- GSHEET_NAME: Target spreadsheet name (used if ID not set; will create if missing)
- GSHEET_WORKSHEET: Worksheet name (default "Leads")

OAuth fallback (use this if you prefer OAuth instead of a service account):
- OAUTH_CLIENT_SECRETS_PATH: Path to `credentials.json` (OAuth client)
- OAUTH_TOKEN_PATH: Path to store `token.json` (default `token.json`)

- HEADLESS: true/false for Playwright (default false)
- STORAGE_STATE_PATH: Path to save/load login cookies (default .playwright/storage_state.json)
- SLOW_MO_MS: Playwright slow motion (ms)
- NAVIGATION_TIMEOUT_MS: Navigation timeout (ms)
- USE_PERSISTENT_CONTEXT: true/false to use persistent user data dir (default true)
- USER_DATA_DIR: Directory for persistent profile (default .playwright/user-data)
- BROWSER_CHANNEL: Browser channel (e.g., chrome) to use the installed Chrome

If both `GCP_SERVICE_ACCOUNT_JSON` and `GCP_SERVICE_ACCOUNT_JSON_PATH` are set, the inline JSON is used.

Example:
```
GSHEET_ID=1No7dGk6fjc4y-1jpSQ17j7Ea12vG_Q5mU3ndjsQe61w
GSHEET_WORKSHEET=Leads
```


