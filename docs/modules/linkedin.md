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

## Recent Fixes

### Profile Link Selector Update (2024)
- **Issue**: LinkedIn changed CSS class names from `app-aware-link` to hashed class names like `lKjZTnOGZpaOgeqHtLwwJwkZOKnITpj`
- **Solution**: Updated selectors to use `a[href*='/in/']` as primary selector with fallback to `a.app-aware-link[href*='/in/']`
- **Impact**: Fixes profile collection in search results that was returning 0 profiles
- **Files Modified**: `automation/linkedin.py`

### Pagination Implementation (2024)
- **Issue**: The `search_people` method was only scrolling on the first page, not moving to subsequent pages
- **Solution**: Implemented pagination logic that automatically moves to next page (`&page=2`, `&page=3`, etc.) when no new profiles are found
- **Features**:
  - Detects stagnant rounds (no new profiles found after scrolling)
  - Automatically navigates to next page using `&page=N` parameter
  - Limits scroll rounds per page to prevent infinite loops
  - Provides detailed logging for debugging
- **Impact**: Significantly increases the number of profiles that can be collected
- **Files Modified**: `automation/linkedin.py`

### Connection Status Filtering (2024)
- **Issue**: The system was collecting all profiles regardless of connection status
- **Solution**: Added filtering to only collect unconnected profiles by checking button text
- **Features**:
  - Filters out profiles with "Message" button (already connected)
  - Only adds profiles with "Connect" or "Follow" button (not connected)
  - Graceful fallback if button status cannot be determined
  - Detailed logging for connection status checks
- **Impact**: Focuses on unconnected profiles, improving efficiency
- **Files Modified**: `automation/linkedin.py`

### MAX_PROFILES Processing Limit (2024)
- **Issue**: System continued processing beyond MAX_PROFILES limit
- **Solution**: Added strict processing limit that stops after reaching MAX_PROFILES
- **Features**:
  - Stops processing after reaching MAX_PROFILES count
  - Updates Google Sheets with collected data
  - Provides detailed logging of processing progress
  - Breaks from processing loop when limit is reached
- **Impact**: Respects user-defined limits and prevents unnecessary processing
- **Files Modified**: `automation/orchestrator.py`


