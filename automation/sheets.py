from __future__ import annotations

import json
from typing import Optional, List, Dict, Any

import gspread
import logging
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
            try:
                self.spreadsheet = client.open_by_key(spreadsheet_id)
                logging.info("Successfully opened spreadsheet with ID: %s", spreadsheet_id)
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 403:
                    logging.error("Permission denied accessing spreadsheet. Please share the sheet with your service account email.")
                    logging.error("Check your service_account.json for the 'client_email' field and share the sheet with that email.")
                raise
        else:
            try:
                self.spreadsheet = client.open(spreadsheet_name)
            except gspread.exceptions.SpreadsheetNotFound:
                # Create a new spreadsheet with the provided name
                logging.info("Spreadsheet '%s' not found. Creating new spreadsheet.", spreadsheet_name)
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
                "connect_sent",
                "connection_accepted",  # For future implementation
            ])

    def append_lead(self, row: List[Any]) -> int:
        """Append a lead to the sheet and return the row number."""
        logging.debug("Appending lead to sheet: %s", row[:4])
        self.worksheet.append_row(row, value_input_option="RAW")
        # Return the row number (1-indexed, header is row 1)
        return len(self.worksheet.get_all_values())
    
    def update_row(self, row_num: int, column_updates: Dict[str, Any]) -> None:
        """Update specific columns in a row.
        
        Args:
            row_num: The row number to update (1-indexed)
            column_updates: Dictionary mapping column names to new values
        """
        # Get header row to find column indices
        headers = self.worksheet.row_values(1)
        
        # Build list of updates (cell address, value)
        updates = []
        for col_name, value in column_updates.items():
            if col_name in headers:
                col_idx = headers.index(col_name) + 1  # 1-indexed
                # Convert column index to letter(s) (A, B, ..., Z, AA, AB, ...)
                cell_address = self._col_num_to_letter(col_idx) + str(row_num)
                updates.append((cell_address, value))
        
        # Batch update all cells
        if updates:
            # Use batch_update for better performance
            batch_data = []
            for cell_addr, val in updates:
                batch_data.append({'range': cell_addr, 'values': [[val]]})
            if batch_data:
                self.worksheet.batch_update(batch_data, value_input_option="RAW")
            logging.debug("Updated row %d with %d values", row_num, len(updates))
    
    def _col_num_to_letter(self, col_num: int) -> str:
        """Convert a column number (1-indexed) to letter(s)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
        return result
    
    def update_cell(self, row_num: int, col_name: str, value: Any) -> None:
        """Update a single cell in the sheet.
        
        Args:
            row_num: The row number to update (1-indexed)
            col_name: The column name
            value: The new value
        """
        self.update_row(row_num, {col_name: value})


