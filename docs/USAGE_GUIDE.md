# LinkedIn Automation Usage Guide

## Quick Setup

1. **Environment Variables**
   Create a `.env` file with:
   ```
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   SEARCH_KEYWORDS=software engineer, founder, cto
   GOOGLE_API_KEY=your_gemini_api_key
   GSHEET_ID=your_google_sheet_id
   GCP_SERVICE_ACCOUNT_JSON_PATH=service_account.json
   
   # Test Mode (set to false to actually send connections)
   TEST_MODE=true
   
   # Optional
   MAX_PROFILES=10
   DEBUG=true
   HEADLESS=false
   ```

2. **Google Sheets Setup**
   - Create a new Google Sheet or use existing one
   - Share it with your service account email (found in service_account.json)
   - Copy the Sheet ID from the URL
   - The system will automatically create headers if the sheet is empty

## Running the Automation

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the automation
python main.py
```

## Google Sheets Structure

The automation creates a comprehensive table with these columns:

| Column | Description |
|--------|-------------|
| **Name** | Profile name |
| **Position** | Extracted job title |
| **Headline** | Full LinkedIn headline |
| **Location** | Geographic location |
| **Profile URL** | LinkedIn profile link |
| **Popularity Score** | AI-calculated score (0-100) |
| **Summary** | AI-generated profile summary |
| **Connection Note** | Personalized connection message |
| **Connect Sent** | Whether connection was sent (yes/no) |
| **Connection Status** | Current status (connected/not_connected/unknown) |
| **Date Added** | When profile was first added |
| **Last Updated** | Most recent update timestamp |
| **About** | Profile about section |
| **Experience** | Work experience list |
| **Education** | Education history |
| **Skills** | Listed skills |

## Features

### 🔍 Smart Profile Collection
- **Duplicate Detection**: Won't add the same profile twice
- **Auto-Update**: Updates existing profiles with new information
- **Connection Filtering**: Skips already connected profiles

### 🤖 AI Features
- **Profile Summaries**: AI analyzes and summarizes each profile
- **Personalized Notes**: Generates custom connection messages
- **Popularity Scoring**: Rates profiles based on seniority and influence

### 🔧 Connection Management
- **Test Mode**: By default, fills connection notes but doesn't send (TEST_MODE=true)
- **Production Mode**: Set TEST_MODE=false to actually send connections
- **Smart Detection**: Multiple methods to find Connect button
- **Note Handling**: Properly handles LinkedIn's "Add a note" dialog

## Troubleshooting

### Headers Not Showing in Google Sheets
The system automatically adds headers if:
- The sheet is completely empty
- Headers are incomplete (less than 16 columns)
- Headers don't match expected format

If you still don't see headers:
1. Clear the sheet completely
2. Run the automation again
3. Headers will be added automatically

### Connection Button Not Found
The system tries multiple methods:
1. aria-label selector: `button[aria-label*="Invite"][aria-label*="to connect"]`
2. Text selector: `button:has(span:text("Connect"))`
3. Role-based selector: `button[role="button"][name="Connect"]`
4. Checks "More actions" dropdown

### Add Note Button Not Working
After clicking Connect, the system:
1. Waits for the modal to appear
2. Clicks "Add a note" button
3. Fills the textarea with your personalized message
4. In test mode: Closes without sending
5. In production: Clicks Send

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `TEST_MODE` | true | When true, doesn't send actual connections |
| `MAX_PROFILES` | 25 | Maximum profiles to process |
| `HEADLESS` | false | Run browser in headless mode |
| `DEBUG` | false | Enable detailed logging |
| `MIN_ACTION_DELAY_MS` | 0 | Minimum delay between actions |
| `MAX_ACTION_DELAY_MS` | 0 | Maximum delay between actions |
| `BROWSER_CHANNEL` | chrome | Browser to use (chrome/chromium/msedge) |

## Best Practices

1. **Start in Test Mode**: Always test first with `TEST_MODE=true`
2. **Small Batches**: Start with `MAX_PROFILES=5` to test
3. **Monitor Logs**: Enable `DEBUG=true` for detailed information
4. **Rate Limiting**: Use action delays to avoid detection
5. **Regular Updates**: Pull latest changes for bug fixes

## Safety Notes

- **LinkedIn ToS**: Automation may violate LinkedIn's Terms of Service
- **Rate Limits**: Don't process too many profiles at once
- **Account Safety**: Use test mode first, monitor your account
- **Data Privacy**: Keep your service account credentials secure

## Common Issues

### "Profile already exists at row X"
This is normal - the system is detecting duplicates and updating instead of adding.

### "Worksheet has incomplete headers"
The system will automatically fix this by replacing headers.

### "Could not find Send button"
Usually happens in test mode - this is intentional to prevent accidental sends.

### "TEST MODE: Not sending connection request"
This is expected behavior when TEST_MODE=true. Set to false to actually send.

## Support

For issues or questions:
1. Check the logs with `DEBUG=true`
2. Review this guide
3. Check the test results: `python -m pytest tests/`
4. Report issues with full error logs