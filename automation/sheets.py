from __future__ import annotations

import json
from typing import Optional, List, Dict, Any

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _credentials_from_settings(json_path: Optional[str], json_blob: Optional[str]) -> Credentials:
    if json_blob:
        info = json.loads(json_blob)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    if json_path:
        return Credentials.from_service_account_file(json_path, scopes=SCOPES)
    raise ValueError("Provide GCP_SERVICE_ACCOUNT_JSON or GCP_SERVICE_ACCOUNT_JSON_PATH for Google Sheets.")


class SheetsClient:
    def __init__(self, json_path: Optional[str], json_blob: Optional[str], spreadsheet_name: str, worksheet_name: str) -> None:
        creds = _credentials_from_settings(json_path, json_blob)
        client = gspread.authorize(creds)

        self.spreadsheet = client.open(spreadsheet_name)
        try:
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            self.worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            self.worksheet.append_row([
                "name",
                "headline",
                "location",
                "profile_url",
                "popularity_score",
                "summary",
                "note",
                "connected",
            ])

    def append_lead(self, row: List[Any]) -> None:
        self.worksheet.append_row(row, value_input_option="RAW")


