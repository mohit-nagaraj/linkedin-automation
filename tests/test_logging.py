import asyncio
import logging

import automation.orchestrator as orch


def test_orchestrator_enables_logging(monkeypatch, caplog):
    # Minimal env
    monkeypatch.setenv("LINKEDIN_EMAIL", "u")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "p")
    monkeypatch.setenv("SEARCH_KEYWORDS", "cto")
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("GSHEET_NAME", "Leads")
    monkeypatch.setenv("DEBUG", "1")

    class DummyLI:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def login(self):
            logging.info("login called")
        async def search_people(self, k, l, max_results=25):
            logging.info("search called")
            return ["https://x/in/a"]
        async def scrape_profile(self, url):
            from automation.linkedin import Profile
            return Profile("n","h","loc",url,"about",[],[],100)
        async def connect_with_note(self, url, note):
            logging.info("connect called")
            return True

    class DummySheets:
        def append_lead(self, row):
            logging.info("sheet append")

    class DummyGemini:
        async def summarize_profile(self, p, b):
            logging.info("summarize called")
            return "s"
        async def craft_connect_note(self, p, b):
            logging.info("note called")
            return "n"

    monkeypatch.setenv("GSHEET_ID", "abc")
    monkeypatch.setattr(orch, "SheetsClient", lambda **kwargs: DummySheets())
    monkeypatch.setattr(orch, "GeminiClient", lambda **kwargs: DummyGemini())
    monkeypatch.setattr(orch, "LinkedInAutomation", lambda **kwargs: DummyLI())

    caplog.set_level(logging.INFO)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(orch.run())
        # Ensure key actions logged
        messages = " ".join(r.message for r in caplog.records)
        assert "Starting LinkedIn login" in messages
        assert "Found 1 profiles" in messages
    finally:
        loop.close()


