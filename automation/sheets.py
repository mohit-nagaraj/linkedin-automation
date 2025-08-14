from __future__ import annotations

import json
from typing import Optional, List, Dict, Any

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _service_account_creds(json_path: Optional[str], json_blob: Optional[str]) -> Optional[Credentials]:
    if json_blob:
        info = json.loads(json_blob)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    if json_path:
        return Credentials.from_service_account_file(json_path, scopes=SCOPES)
    return None


def _oauth_user_creds(client_secrets_path: Optional[str], token_path: str) -> Optional[UserCredentials]:
    if not client_secrets_path:
        return None
    creds: Optional[UserCredentials] = None
    try:
        import os
        if os.path.exists(token_path):
            creds = UserCredentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        return creds
    except Exception:
        return None


class SheetsClient:
    def __init__(self, json_path: Optional[str], json_blob: Optional[str], spreadsheet_name: str, worksheet_name: str,
                 oauth_client_secrets_path: Optional[str] = None, oauth_token_path: str = "token.json",
                 spreadsheet_id: Optional[str] = None) -> None:
        creds = _service_account_creds(json_path, json_blob)
        if creds is None:
            user_creds = _oauth_user_creds(oauth_client_secrets_path, oauth_token_path)
            if user_creds is None:
                raise ValueError("Google Sheets credentials not configured. Provide service account JSON or set OAUTH_CLIENT_SECRETS_PATH for OAuth.")
            client = gspread.authorize(user_creds)
        else:
            client = gspread.authorize(creds)

        # Open by ID if provided, else by name; if not found by name, create it
        if spreadsheet_id:
            self.spreadsheet = client.open_by_key(spreadsheet_id)
        else:
            try:
                self.spreadsheet = client.open(spreadsheet_name)
            except gspread.exceptions.SpreadsheetNotFound:
                # Create a new spreadsheet with the provided name
                self.spreadsheet = client.create(spreadsheet_name)
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


