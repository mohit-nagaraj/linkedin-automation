## Google Sheets client

File: `automation/sheets.py`

Responsibilities:
- Authenticate with Google via a service account
- Open or create the worksheet
- Append a row per processed lead

Setup:
- Create a Google Cloud service account
- Download JSON key or embed as `GCP_SERVICE_ACCOUNT_JSON`
- Share the target spreadsheet with the service account email (Editor)

Schema:
- **name**: Profile name
- **headline**: Job title/headline
- **location**: Location
- **profile_url**: LinkedIn profile URL
- **popularity_score**: Calculated popularity score (0-100)
- **summary**: AI-generated profile summary
- **note**: AI-generated connection note
- **connected**: "yes" or "no" (connection status)

### Recent Updates
- **MAX_PROFILES Processing**: Stops processing after reaching the specified limit
- **Real-time Updates**: Each profile is added to sheets immediately after processing
- **Error Handling**: Graceful handling of connection failures and API errors
- **Detailed Logging**: Comprehensive logging for debugging and monitoring


