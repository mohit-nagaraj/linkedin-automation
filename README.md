# linkedin-automation

[![CI](https://img.shields.io/badge/tests-passing-brightgreen)](docs/testing.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Python-based LinkedIn lead finder and connector for software dev/founder personas. It:

- Logs into LinkedIn, searches people by your keywords with **pagination support**
- **Filters by connection status** - only processes unconnected profiles
- Scrapes comprehensive profile info (name, position, headline, location, about, experiences, education, skills, followers)
- **Smart duplicate detection** - updates existing profiles instead of creating duplicates
- Uses Google Gemini 2.5 Flash to generate a concise profile summary and a personalized 280-char connect note
- Sends a connection request with note (with test mode available)
- Stores leads into Google Sheets with **enhanced table structure** for better tracking
- **Respects MAX_PROFILES limit** - stops processing after reaching your specified limit

Note: Automating LinkedIn may violate their Terms. Use responsibly and at your own risk.

## Quickstart

- Copy `.env.example` to `.env` and set `GSHEET_ID` from your sheet URL
- More config: see `docs/config.md`
- Install deps: `& ".venv\\Scripts\\pip" install -r requirements.txt`
- Run: `python main.py`
- Tests: `& ".venv\\Scripts\\python" -m pytest` (see `docs/testing.md`)

## Key Features

### 🔍 Smart Profile Collection
- **Connection Status Filtering**: Automatically skips already connected profiles
- **Pagination Support**: Searches across multiple pages for maximum results
- **Enhanced Connect Button Detection**: Multiple methods to find and click connect buttons
- **Robust Selectors**: Multiple fallback selectors for LinkedIn's changing DOM

### 📊 Processing Control
- **MAX_PROFILES Limit**: Set your processing limit in environment variables
- **Duplicate Detection**: Checks if profile URL already exists before adding
- **Real-time Updates**: Each profile is processed and updated in sheets immediately
- **Detailed Logging**: Comprehensive logging with visibility into all operations

### 🤖 AI-Powered Personalization
- **Smart Summaries**: AI-generated profile summaries using Google Gemini
- **Personalized Notes**: Custom connection notes based on profile analysis
- **Popularity Scoring**: Intelligent scoring based on followers, skills, and experience

### 📋 Enhanced Google Sheets Integration
- **Comprehensive Columns**: Name, Position, Headline, Location, Profile URL, Score, Summary, Note, and more
- **Tracking Fields**: Date Added, Last Updated, Connection Status, and Connection Sent
- **Profile Details**: About section, Experience, Education, and Skills stored
- **Smart Updates**: Updates existing rows if profile URL already exists

## Mohit bio used for personalization

Hardcoded in `automation/orchestrator.py` as `OWNER_BIO`. Edit to your preference.

## Caution

- Respect LinkedIn’s terms and local laws.
- UI selectors on LinkedIn change often; locators may need tweaks.
- Use responsibly and consider rate limiting for large-scale operations.

See more in `docs/`.

