"""Tests for enhanced sheets functionality."""
import json
import pytest
from unittest.mock import MagicMock, patch
from automation.sheets import SheetsClient


class MockWorksheet:
    def __init__(self):
        self.data = []
        self.headers = []
    
    def get_all_values(self):
        """Return all rows including headers."""
        if self.headers:
            return [self.headers] + self.data
        return self.data
    
    def row_values(self, row_num):
        """Get values for a specific row (1-indexed)."""
        all_values = self.get_all_values()
        if 0 < row_num <= len(all_values):
            return all_values[row_num - 1]
        return []
    
    def append_row(self, row, value_input_option=None):
        """Append a row to the worksheet."""
        if not self.headers:
            self.headers = row
        else:
            self.data.append(row)
    
    def batch_update(self, batch_data, value_input_option=None):
        """Mock batch update."""
        pass
    
    def delete_rows(self, row_num):
        """Delete a row from the worksheet (1-indexed)."""
        all_values = self.get_all_values()
        if row_num == 1 and self.headers:
            self.headers = []
        elif row_num > 1 and row_num <= len(all_values):
            self.data.pop(row_num - 2)  # -2 because data is 0-indexed and skips header
    
    def insert_row(self, row, index=1):
        """Insert a row at the given index (1-indexed)."""
        if index == 1:
            self.headers = row
        else:
            self.data.insert(index - 2, row)  # -2 because data is 0-indexed and skips header


class MockSpreadsheet:
    def __init__(self):
        self.worksheets = {}
    
    def worksheet(self, name):
        if name not in self.worksheets:
            from automation.sheets import gspread
            raise gspread.exceptions.WorksheetNotFound(f"Worksheet {name} not found")
        return self.worksheets[name]
    
    def add_worksheet(self, title, rows, cols):
        ws = MockWorksheet()
        self.worksheets[title] = ws
        return ws


def test_find_row_by_url(monkeypatch):
    """Test finding a row by profile URL."""
    # Setup mocks
    mock_client = MagicMock()
    mock_spreadsheet = MockSpreadsheet()
    mock_worksheet = MockWorksheet()
    
    # Add test data with complete headers
    mock_worksheet.headers = [
        "Name", "Position", "Headline", "Location", "Profile URL", 
        "Popularity Score", "Summary", "Connection Note", "Connect Sent",
        "Connection Status", "Date Added", "Last Updated", "About",
        "Experience", "Education", "Skills"
    ]
    mock_worksheet.data = [
        ["John Doe", "Engineer", "Software Engineer", "SF", "https://linkedin.com/in/johndoe",
         "0", "", "", "no", "not_connected", "", "", "", "", "", ""],
        ["Jane Smith", "Manager", "Product Manager", "NYC", "https://linkedin.com/in/janesmith",
         "0", "", "", "no", "not_connected", "", "", "", "", "", ""],
    ]
    
    mock_spreadsheet.worksheets["Leads"] = mock_worksheet
    mock_client.open = MagicMock(return_value=mock_spreadsheet)
    
    # Patch gspread
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_info", 
                       lambda info, scopes: "creds")
    monkeypatch.setattr("automation.sheets.gspread.authorize", 
                       lambda creds: mock_client)
    
    # Create SheetsClient
    sc = SheetsClient(
        json_path=None,
        json_blob=json.dumps({"type": "service_account"}),
        spreadsheet_name="Test",
        worksheet_name="Leads"
    )
    
    # Test finding existing URL
    row_num = sc.find_row_by_url("https://linkedin.com/in/johndoe")
    assert row_num == 2  # First data row (header is row 1)
    
    row_num = sc.find_row_by_url("https://linkedin.com/in/janesmith")
    assert row_num == 3  # Second data row
    
    # Test non-existent URL
    row_num = sc.find_row_by_url("https://linkedin.com/in/nonexistent")
    assert row_num is None


def test_update_row(monkeypatch):
    """Test updating specific columns in a row."""
    # Setup mocks
    mock_client = MagicMock()
    mock_spreadsheet = MockSpreadsheet()
    mock_worksheet = MockWorksheet()
    
    # Add test data with complete headers
    mock_worksheet.headers = [
        "Name", "Position", "Headline", "Location", "Profile URL", 
        "Popularity Score", "Summary", "Connection Note", "Connect Sent",
        "Connection Status", "Date Added", "Last Updated", "About",
        "Experience", "Education", "Skills"
    ]
    mock_worksheet.data = [
        ["John Doe", "Engineer", "Software Engineer", "SF", "https://linkedin.com/in/johndoe",
         "0", "", "", "pending", "not_connected", "", "", "", "", "", ""],
    ]
    
    # Mock batch_update to track calls
    update_calls = []
    def mock_batch_update(batch_data, value_input_option=None):
        update_calls.append(batch_data)
    
    mock_worksheet.batch_update = mock_batch_update
    mock_spreadsheet.worksheets["Leads"] = mock_worksheet
    mock_client.open = MagicMock(return_value=mock_spreadsheet)
    
    # Patch gspread
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_info", 
                       lambda info, scopes: "creds")
    monkeypatch.setattr("automation.sheets.gspread.authorize", 
                       lambda creds: mock_client)
    
    # Create SheetsClient
    sc = SheetsClient(
        json_path=None,
        json_blob=json.dumps({"type": "service_account"}),
        spreadsheet_name="Test",
        worksheet_name="Leads"
    )
    
    # Test updating multiple columns
    sc.update_row(2, {
        "Popularity Score": "85",
        "Connection Status": "completed"
    })
    
    # Verify batch update was called with correct data
    assert len(update_calls) == 1
    batch_data = update_calls[0]
    assert len(batch_data) == 2
    
    # Check that correct cells are being updated
    cell_updates = {item['range']: item['values'][0][0] for item in batch_data}
    assert 'F2' in cell_updates  # Popularity Score column (F) row 2
    assert 'J2' in cell_updates  # Connection Status column (J) row 2
    assert cell_updates['F2'] == "85"
    assert cell_updates['J2'] == "completed"


def test_column_number_to_letter():
    """Test converting column numbers to letters."""
    sc = SheetsClient.__new__(SheetsClient)
    
    # Test single letters
    assert sc._col_num_to_letter(1) == "A"
    assert sc._col_num_to_letter(26) == "Z"
    
    # Test double letters
    assert sc._col_num_to_letter(27) == "AA"
    assert sc._col_num_to_letter(28) == "AB"
    assert sc._col_num_to_letter(52) == "AZ"
    assert sc._col_num_to_letter(53) == "BA"


def test_new_headers_structure(monkeypatch):
    """Test that new sheets are created with the updated header structure."""
    # Setup mocks
    mock_client = MagicMock()
    mock_spreadsheet = MockSpreadsheet()
    mock_client.open = MagicMock(return_value=mock_spreadsheet)
    
    # Track worksheet creation
    created_worksheets = []
    original_add_worksheet = mock_spreadsheet.add_worksheet
    def track_add_worksheet(title, rows, cols):
        ws = original_add_worksheet(title, rows, cols)
        created_worksheets.append((title, ws))
        return ws
    
    mock_spreadsheet.add_worksheet = track_add_worksheet
    
    # Patch gspread
    from types import SimpleNamespace
    
    class WorksheetNotFound(Exception):
        pass
    
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_info", 
                       lambda info, scopes: "creds")
    monkeypatch.setattr("automation.sheets.gspread", 
                       SimpleNamespace(
                           authorize=lambda creds: mock_client,
                           exceptions=SimpleNamespace(WorksheetNotFound=WorksheetNotFound)
                       ))
    
    # Create SheetsClient (will create new worksheet)
    sc = SheetsClient(
        json_path=None,
        json_blob=json.dumps({"type": "service_account"}),
        spreadsheet_name="Test",
        worksheet_name="NewLeads"
    )
    
    # Verify worksheet was created
    assert len(created_worksheets) == 1
    assert created_worksheets[0][0] == "NewLeads"
    
    # Verify headers were added
    ws = mock_spreadsheet.worksheets["NewLeads"]
    headers = ws.headers
    
    # Check for new columns
    assert "Name" in headers
    assert "Position" in headers
    assert "Headline" in headers
    assert "Profile URL" in headers
    assert "Summary" in headers
    assert "Connection Note" in headers
    assert "Date Added" in headers
    assert "Last Updated" in headers
    assert "About" in headers
    assert "Experience" in headers
    assert "Education" in headers
    assert "Skills" in headers