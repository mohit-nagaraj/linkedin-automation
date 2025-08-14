import os
from automation.config import load_settings


def test_runtime_defaults_and_env(monkeypatch):
    # Defaults (no env): headless should be false, persistent true, chrome channel
    s = load_settings()
    assert s.headless is False
    assert s.use_persistent_context is True
    assert s.browser_channel == "chrome"

    # Env overrides
    monkeypatch.setenv("HEADLESS", "true")
    monkeypatch.setenv("USE_PERSISTENT_CONTEXT", "false")
    monkeypatch.setenv("USER_DATA_DIR", ".tmp/profile")
    monkeypatch.setenv("BROWSER_CHANNEL", "msedge")
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("MIN_ACTION_DELAY_MS", "100")
    monkeypatch.setenv("MAX_ACTION_DELAY_MS", "300")
    s2 = load_settings()
    assert s2.headless is True
    assert s2.use_persistent_context is False
    assert s2.user_data_dir == ".tmp/profile"
    assert s2.browser_channel == "msedge"
    assert s2.debug is True
    assert s2.min_action_delay_ms == 100
    assert s2.max_action_delay_ms == 300


