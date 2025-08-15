import asyncio
from types import SimpleNamespace

import automation.orchestrator as orch


class DummyLI:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def login(self):
        pass
    async def search_people_listings(self, keywords, locations, max_results=25):
        from automation.linkedin import SearchResult
        return [SearchResult(name="Jane", headline="CTO", location="Remote", profile_url="https://www.linkedin.com/in/jane")]
    async def scrape_profile(self, url):
        from automation.linkedin import Profile
        return Profile(
            name="Jane",
            headline="CTO",
            location="Remote",
            profile_url=url,
            about="about",
            experiences=["a"],
            skills=["go"],
            followers_count=100,
        )
    async def connect_with_note(self, url, note):
        return True


class DummySheets:
    def __init__(self):
        self.rows = []
    def append_lead(self, row):
        self.rows.append(row)


class DummyGemini:
    async def summarize_profile(self, profile, owner_bio):
        return "summary"
    async def craft_connect_note(self, profile, owner_bio):
        return "note"


def test_orchestrator_main_flow(monkeypatch):
    # Env
    monkeypatch.setenv("LINKEDIN_EMAIL", "u")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "p")
    monkeypatch.setenv("SEARCH_KEYWORDS", "cto")
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("GSHEET_NAME", "Leads")
    # debug and delays
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("MIN_ACTION_DELAY_MS", "100")
    monkeypatch.setenv("MAX_ACTION_DELAY_MS", "200")

    dummy_sheets = DummySheets()

    monkeypatch.setattr(orch, "SheetsClient", lambda **kwargs: dummy_sheets)
    monkeypatch.setattr(orch, "GeminiClient", lambda **kwargs: DummyGemini())
    monkeypatch.setattr(orch, "LinkedInAutomation", lambda **kwargs: DummyLI())

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(orch.run())
        assert len(dummy_sheets.rows) == 1
        assert dummy_sheets.rows[0][0] == "Jane"
        assert dummy_sheets.rows[0][-1] == "yes"
    finally:
        loop.close()


