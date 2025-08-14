## Runbook

1. Create `.env` (see `docs/config.md`)
2. Create venv and install requirements
3. Install Playwright Chromium
4. Ensure Google Sheet is shared with the service account
5. Run `python main.py`

Operational tips:
- First run saves `STORAGE_STATE_PATH`; subsequent runs reuse session
- Set `HEADLESS=false` and `SLOW_MO_MS=200` to observe behavior
- If login loops, delete storage state and retry
- UI changes on LinkedIn can break locators; adjust in `automation/linkedin.py`
- Be mindful of LinkedIn ToS; keep volumes low and human-like


