## Testing and coverage

- Test framework: pytest with pytest-asyncio and pytest-cov
- Coverage target: ≥85%

Run:
```bash
& ".venv\Scripts\python" -m pytest
```

### Test Categories

#### Core Functionality Tests
- **Config Tests**: Environment variable parsing and validation
- **LinkedIn Tests**: Selector fixes, pagination, connection filtering
- **Orchestrator Tests**: Full workflow simulation with mock components
- **Sheets Tests**: Google Sheets integration and data structure validation

#### Integration Tests
- **Connection Filtering**: Tests for profile filtering based on connection status
- **Pagination**: Tests for multi-page search functionality
- **Sheets Updates**: Tests for Google Sheets data structure and updates

#### Unit Tests
- **Scoring**: Popularity score calculation algorithms
- **Gemini Client**: AI-powered summary and note generation
- **Logging**: Logging configuration and output validation

### Test Highlights
- Unit tests for config parsing, scoring, Sheets client, Gemini client
- Orchestrator test uses fakes to simulate full run without network/browser
- Browser driver (`automation/linkedin.py`) omitted from coverage by default (`.coveragerc`)
- Integration tests for new features like connection filtering and pagination
- Mock-based tests for external services (Google Sheets, Gemini API)


