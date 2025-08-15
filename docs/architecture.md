## Architecture

### Components
- `automation/config.py`: reads env, builds `Settings`
- `automation/linkedin.py`: Playwright login/session, search, scrape, connect
- `automation/gemini_client.py`: summaries + connection notes
- `automation/scoring.py`: popularity score
- `automation/sheets.py`: Google Sheets append
- `automation/orchestrator.py`: orchestrates the flow

### Data flow
1. Load `.env` and environment variables
2. Start LinkedInAutomation (reuse storage state if present)
3. Search people → collect profile URLs (with connection status filtering)
4. For each URL (up to MAX_PROFILES): scrape → score → summarize → craft note
5. Attempt connect with note
6. Append result row to Google Sheet
7. Stop processing when MAX_PROFILES limit is reached

### Sequence
```mermaid
sequenceDiagram
  participant U as "You"
  participant O as "Orchestrator"
  participant L as "LinkedInAutomation"
  participant G as "GeminiClient"
  participant S as "SheetsClient"

  U->>O: python main.py
  O->>L: login (reuse storage_state)
  L-->>O: ok
  O->>L: search_people(keywords)
  L-->>O: [profile_urls]
  loop each profile
    O->>L: scrape_profile(url)
    L-->>O: Profile
    O->>G: summarize_profile(Profile)
    G-->>O: Summary
    O->>G: craft_connect_note(Profile)
    G-->>O: Note
    O->>L: connect_with_note(url, note)
    L-->>O: connected?
    O->>S: append_lead(row)
  end
```

### Storage state
- Reuses Playwright `storage_state.json` to avoid re-login
- Saved after successful login

### Key Features
- **Connection Status Filtering**: Only processes unconnected profiles (filters out "Message" button profiles)
- **Pagination Support**: Automatically moves to next page when no new profiles found
- **MAX_PROFILES Limit**: Respects user-defined processing limits
- **Robust Selectors**: Multiple fallback selectors for LinkedIn's changing DOM
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

### Notes
- LinkedIn DOM changes; locators may need updates
- Add throttling/random delays if extending volume
- Connection status filtering improves efficiency by focusing on unconnected profiles
- Pagination ensures maximum profile collection across multiple search pages


