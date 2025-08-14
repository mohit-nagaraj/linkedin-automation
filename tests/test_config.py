import os
from automation.config import load_settings


def test_load_settings_reads_env(monkeypatch):
    monkeypatch.setenv("LINKEDIN_EMAIL", "user@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "secret")
    monkeypatch.setenv("SEARCH_KEYWORDS", "software engineer, founder")
    monkeypatch.setenv("LOCATIONS", "Remote,India")
    monkeypatch.setenv("SENIORITY_KEYWORDS", "cto,founder")
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GSHEET_NAME", "Leads")
    monkeypatch.setenv("GSHEET_WORKSHEET", "Leads")
    monkeypatch.setenv("STORAGE_STATE_PATH", ".playwright/storage_state.json")

    s = load_settings()
    assert s.linkedin_email == "user@example.com"
    assert s.search_keywords == ["software engineer", "founder"]
    assert s.locations == ["Remote", "India"]
    assert s.seniority_keywords == ["cto", "founder"]
    assert s.storage_state_path.endswith("storage_state.json")


