## Gemini client

File: `automation/gemini_client.py`

Responsibilities:
- Configure Gemini with API key
- Generate concise profile summaries
- Craft short, specific 280-char connection notes

Notes:
- Model: `gemini-1.5-flash`
- Prompts focus on concrete details
- Generation invoked via `asyncio.to_thread` to avoid blocking
- Import is lazy/injectable for testability

### Recent Updates
- **Enhanced Error Handling**: Better error handling for API failures
- **Improved Prompts**: More focused prompts for better summary and note quality
- **Async Processing**: Non-blocking API calls for better performance
- **Integration with MAX_PROFILES**: Respects processing limits


