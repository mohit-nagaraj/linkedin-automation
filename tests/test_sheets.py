import json
from types import SimpleNamespace

from automation.sheets import SheetsClient


class DummyWorksheet:
    def __init__(self):
        self.rows = []

    def append_row(self, row, value_input_option=None):
        self.rows.append(row)
    
    def get_all_values(self):
        return self.rows
    
    def row_values(self, row_num):
        if row_num > 0 and row_num <= len(self.rows):
            return self.rows[row_num - 1]
        return []
    
    def batch_update(self, batch_data, value_input_option=None):
        for update in batch_data:
            # Simple implementation for testing
            pass


class WorksheetNotFound(Exception):
    pass


class DummySpreadsheet:
    def __init__(self):
        self.by_title = {}

    def worksheet(self, name):
        if name not in self.by_title:
            raise WorksheetNotFound("WorksheetNotFound")
        return self.by_title[name]

    def add_worksheet(self, title, rows, cols):
        ws = DummyWorksheet()
        # Don't add header here - the SheetsClient will do it
        self.by_title[title] = ws
        return ws


class DummyClient:
    def __init__(self):
        self.opened = None
        self.opened_by_key = None
        self.sheet = DummySpreadsheet()

    def open(self, name):
        self.opened = name
        return self.sheet
    
    def open_by_key(self, key):
        self.opened_by_key = key
        return self.sheet


def test_sheets_client_appends(monkeypatch):
    # Fake credentials creation and gspread.authorize
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_info", lambda info, scopes: "creds")
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_file", lambda path, scopes: "creds")
    # Ensure WorksheetNotFound resolves to our custom WorksheetNotFound
    from types import SimpleNamespace
    monkeypatch.setattr("automation.sheets.gspread", SimpleNamespace(
        authorize=lambda creds: None, 
        exceptions=SimpleNamespace(WorksheetNotFound=WorksheetNotFound)
    ))
    # But we still want authorize to return our dummy client
    dummy_client = DummyClient()
    def fake_authorize(_):
        return dummy_client
    monkeypatch.setattr("automation.sheets.gspread.authorize", fake_authorize)

    sc = SheetsClient(json_path=None, json_blob=json.dumps({"type": "service_account"}), spreadsheet_name="Book", worksheet_name="Leads")
    # First append will create the worksheet with headers
    row_num1 = sc.append_lead(["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"])
    # A second append to ensure calls work
    row_num2 = sc.append_lead(["q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "1", "2", "3", "4", "5", "6"])

    ws = dummy_client.sheet.by_title["Leads"]
    # Row 0 is the header
    assert ws.rows[0][0] == "Name"  # First column of header
    assert ws.rows[0][4] == "Profile URL"  # Fifth column of header
    # Data rows start at index 1
    assert ws.rows[1] == ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"]
    assert ws.rows[2] == ["q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "1", "2", "3", "4", "5", "6"]
    assert row_num1 == 2  # Row numbers are 1-indexed, header is row 1
    assert row_num2 == 3  # Second data row


