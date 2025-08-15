from __future__ import annotations

import json
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from .profile_extractor import DetailedProfile


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class EnhancedSheetsClient:
    """Enhanced Google Sheets client with comprehensive profile data support"""
    
    # Define comprehensive column structure
    COLUMNS = [
        # Basic Information
        "timestamp",
        "name",
        "headline",
        "location",
        "profile_url",
        
        # About and Summary
        "about",
        "ai_summary",
        "popularity_score",
        
        # Experience and Skills
        "current_position",
        "current_company",
        "total_experience_years",
        "top_skills",
        "all_skills_count",
        "achievements",
        
        # Education and Certifications
        "education",
        "certifications",
        
        # Contact and Social
        "email",
        "website",
        "blogs",
        "github",
        "twitter",
        
        # Networking
        "followers_count",
        "connections_count",
        "mutual_connections",
        
        # Activity
        "recent_post_snippet",
        "interests",
        
        # AI Generated Content
        "inmail_note",
        "ice_breaker_1",
        "ice_breaker_2",
        "ice_breaker_3",
        
        # Outreach Status
        "connect_sent",
        "connect_sent_date",
        "connection_accepted",
        "message_sent",
        "response_received",
        "notes"
    ]
    
    def __init__(self, json_path: Optional[str], json_blob: Optional[str], 
                 spreadsheet_name: str, worksheet_name: str,
                 oauth_client_secrets_path: Optional[str] = None, 
                 oauth_token_path: str = "token.json",
                 spreadsheet_id: Optional[str] = None) -> None:
        
        # Authenticate
        creds = self._get_credentials(json_path, json_blob, oauth_client_secrets_path, oauth_token_path)
        client = gspread.authorize(creds)
        
        # Open or create spreadsheet
        if spreadsheet_id:
            try:
                self.spreadsheet = client.open_by_key(spreadsheet_id)
                logging.info("Opened spreadsheet with ID: %s", spreadsheet_id)
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 403:
                    logging.error("Permission denied. Share the sheet with your service account email.")
                raise
        else:
            try:
                self.spreadsheet = client.open(spreadsheet_name)
            except gspread.exceptions.SpreadsheetNotFound:
                logging.info("Creating new spreadsheet: %s", spreadsheet_name)
                self.spreadsheet = client.create(spreadsheet_name)
        
        # Open or create worksheet
        try:
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
            self._ensure_headers()
        except gspread.exceptions.WorksheetNotFound:
            self.worksheet = self.spreadsheet.add_worksheet(
                title=worksheet_name, 
                rows=5000, 
                cols=len(self.COLUMNS)
            )
            self.worksheet.append_row(self.COLUMNS)
            self._format_headers()
    
    def _get_credentials(self, json_path: Optional[str], json_blob: Optional[str],
                        oauth_client_secrets_path: Optional[str], oauth_token_path: str):
        """Get credentials from service account or OAuth"""
        if json_blob:
            info = json.loads(json_blob)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        if json_path:
            return Credentials.from_service_account_file(json_path, scopes=SCOPES)
        
        # Try OAuth
        if oauth_client_secrets_path:
            return self._get_oauth_creds(oauth_client_secrets_path, oauth_token_path)
        
        raise ValueError("No valid credentials provided")
    
    def _get_oauth_creds(self, client_secrets_path: str, token_path: str) -> UserCredentials:
        """Get OAuth user credentials"""
        import os
        creds = None
        
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
    
    def _ensure_headers(self):
        """Ensure worksheet has all required headers"""
        current_headers = self.worksheet.row_values(1)
        
        # Add any missing columns
        missing_columns = [col for col in self.COLUMNS if col not in current_headers]
        if missing_columns:
            logging.info(f"Adding {len(missing_columns)} new columns to sheet")
            # Expand the sheet if needed
            current_cols = len(current_headers)
            needed_cols = current_cols + len(missing_columns)
            if self.worksheet.col_count < needed_cols:
                self.worksheet.resize(cols=needed_cols)
            
            # Add missing headers
            for i, col in enumerate(missing_columns):
                col_idx = current_cols + i + 1
                self.worksheet.update_cell(1, col_idx, col)
    
    def _format_headers(self):
        """Apply formatting to header row"""
        try:
            # Make headers bold and freeze the row
            fmt = {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "textFormat": {"bold": True}
            }
            self.worksheet.format("1:1", fmt)
        except Exception as e:
            logging.warning(f"Could not format headers: {e}")
    
    def add_profile(self, profile: DetailedProfile, ai_summary: str = "", 
                   popularity_score: float = 0.0) -> int:
        """Add a comprehensive profile to the sheet"""
        
        # Prepare row data matching column order
        row_data = self._profile_to_row(profile, ai_summary, popularity_score)
        
        logging.debug(f"Adding profile to sheet: {profile.name}")
        self.worksheet.append_row(row_data, value_input_option="RAW")
        
        # Return the row number
        return len(self.worksheet.get_all_values())
    
    def _profile_to_row(self, profile: DetailedProfile, ai_summary: str, 
                        popularity_score: float) -> List[Any]:
        """Convert DetailedProfile to row data"""
        
        # Extract current position and company
        current_position = ""
        current_company = ""
        total_exp_years = ""
        if profile.experiences:
            current_exp = profile.experiences[0]
            current_position = current_exp.get("title", "")
            current_company = current_exp.get("company", "")
            # Try to parse years from duration
            duration = current_exp.get("duration", "")
            if "yr" in duration:
                years = [int(s) for s in duration.split() if s.isdigit()]
                if years:
                    total_exp_years = str(years[0])
        
        # Format education
        education_text = ""
        if profile.education:
            edu = profile.education[0]
            education_text = f"{edu.get('degree', '')} - {edu.get('school', '')}"
        
        # Format lists
        skills_text = ", ".join(profile.skills[:10]) if profile.skills else ""
        achievements_text = " | ".join(profile.achievements[:3]) if profile.achievements else ""
        certifications_text = " | ".join(profile.certifications[:3]) if profile.certifications else ""
        mutual_text = ", ".join(profile.mutual_connections[:5]) if profile.mutual_connections else ""
        interests_text = " | ".join(profile.interests[:5]) if profile.interests else ""
        
        # Build row matching COLUMNS order
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # timestamp
            profile.name,
            profile.headline,
            profile.location or "",
            profile.profile_url,
            
            # About and Summary
            (profile.about or "")[:500],  # Truncate long about sections
            ai_summary,
            popularity_score,
            
            # Experience and Skills
            current_position,
            current_company,
            total_exp_years,
            skills_text,
            len(profile.skills),
            achievements_text,
            
            # Education and Certifications
            education_text,
            certifications_text,
            
            # Contact and Social
            profile.email or "",
            profile.website or "",
            ", ".join(profile.blogs) if profile.blogs else "",
            profile.social_links.get("github", ""),
            profile.social_links.get("twitter", ""),
            
            # Networking
            profile.followers_count or 0,
            profile.connections_count or 0,
            mutual_text,
            
            # Activity
            profile.recent_posts[0][:200] if profile.recent_posts else "",
            interests_text,
            
            # AI Generated Content
            profile.inmail_note or "",
            profile.ice_breakers[0] if len(profile.ice_breakers) > 0 else "",
            profile.ice_breakers[1] if len(profile.ice_breakers) > 1 else "",
            profile.ice_breakers[2] if len(profile.ice_breakers) > 2 else "",
            
            # Outreach Status (initially empty)
            "",  # connect_sent
            "",  # connect_sent_date
            "",  # connection_accepted
            "",  # message_sent
            "",  # response_received
            ""   # notes
        ]
        
        return row
    
    def update_profile_status(self, row_num: int, status_updates: Dict[str, Any]) -> None:
        """Update outreach status for a profile"""
        
        # Get header row to find column indices
        headers = self.worksheet.row_values(1)
        
        # Build list of updates
        updates = []
        for col_name, value in status_updates.items():
            if col_name in headers:
                col_idx = headers.index(col_name) + 1  # 1-indexed
                cell_address = self._col_num_to_letter(col_idx) + str(row_num)
                updates.append({'range': cell_address, 'values': [[value]]})
        
        # Batch update
        if updates:
            self.worksheet.batch_update(updates, value_input_option="RAW")
            logging.debug(f"Updated row {row_num} with {len(updates)} status updates")
    
    def mark_connect_sent(self, row_num: int) -> None:
        """Mark that a connection request was sent"""
        self.update_profile_status(row_num, {
            "connect_sent": "Yes",
            "connect_sent_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def mark_connection_accepted(self, row_num: int) -> None:
        """Mark that a connection was accepted"""
        self.update_profile_status(row_num, {
            "connection_accepted": "Yes"
        })
    
    def add_note(self, row_num: int, note: str) -> None:
        """Add a note to a profile"""
        # Get existing notes
        headers = self.worksheet.row_values(1)
        if "notes" in headers:
            col_idx = headers.index("notes") + 1
            current_notes = self.worksheet.cell(row_num, col_idx).value or ""
            
            # Append new note with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] {note}"
            
            if current_notes:
                updated_notes = f"{current_notes}\n{new_note}"
            else:
                updated_notes = new_note
            
            self.update_profile_status(row_num, {"notes": updated_notes})
    
    def get_profiles_pending_connection(self) -> List[Dict[str, Any]]:
        """Get profiles that haven't been contacted yet"""
        all_records = self.worksheet.get_all_records()
        pending = []
        
        for i, record in enumerate(all_records, start=2):  # Start at row 2 (after header)
            if not record.get("connect_sent"):
                record["row_number"] = i
                pending.append(record)
        
        return pending
    
    def _col_num_to_letter(self, col_num: int) -> str:
        """Convert column number to letter(s)"""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
        return result