## Testing and coverage

- Test framework: pytest with pytest-asyncio and pytest-cov
- Coverage target: ≥85%

Run:
```bash
& ".venv\Scripts\python" -m pytest
```

Highlights:
- Unit tests for config parsing, scoring, Sheets client, Gemini client
- Orchestrator test uses fakes to simulate full run without network/browser
- Browser driver (`automation/linkedin.py`) omitted from coverage by default (`.coveragerc`)


