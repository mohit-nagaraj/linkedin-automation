## LinkedIn automation

File: `automation/linkedin.py`

Responsibilities:
- Manage Chromium browser, context, and page
- Reuse session via Playwright storage state
- Login only if needed
- Search people and collect profile URLs
- Scrape profile details (name, headline, location, about, experiences, skills, followers)
- Send connection requests with a personalized note

Key methods:
- `login()`: go to feed; if redirected to login, perform login and save storage
- `search_people(keywords, locations, max_results)`: gather profile URLs from results, scroll to load more
- `scrape_profile(url)`: extract visible fields with conservative selectors
- `connect_with_note(url, note)`: profile → Connect → Add a note → Send

Caveats:
- LinkedIn selectors change frequently; adjust locators as needed
- Some sections may be collapsed/hidden depending on auth state
- Rate-limit actions; use randomized delays for scale


