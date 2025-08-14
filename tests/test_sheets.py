import json
from types import SimpleNamespace

from automation.sheets import SheetsClient


class DummyWorksheet:
    def __init__(self):
        self.rows = []

    def append_row(self, row, value_input_option=None):
        self.rows.append(row)


class DummySpreadsheet:
    def __init__(self):
        self.by_title = {}

    def worksheet(self, name):
        if name not in self.by_title:
            raise Exception("WorksheetNotFound")
        return self.by_title[name]

    def add_worksheet(self, title, rows, cols):
        ws = DummyWorksheet()
        self.by_title[title] = ws
        return ws


class DummyClient:
    def __init__(self):
        self.opened = None
        self.sheet = DummySpreadsheet()

    def open(self, name):
        self.opened = name
        return self.sheet


def test_sheets_client_appends(monkeypatch):
    # Fake credentials creation and gspread.authorize
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_info", lambda info, scopes: "creds")
    monkeypatch.setattr("automation.sheets.Credentials.from_service_account_file", lambda path, scopes: "creds")
    # Ensure WorksheetNotFound resolves to Exception in our dummy
    from types import SimpleNamespace
    monkeypatch.setattr("automation.sheets.gspread", SimpleNamespace(authorize=lambda creds: None, exceptions=SimpleNamespace(WorksheetNotFound=Exception)))
    # But we still want authorize to return our dummy client
    dummy_client = DummyClient()
    def fake_authorize(_):
        return dummy_client
    monkeypatch.setattr("automation.sheets.gspread.authorize", fake_authorize)

    sc = SheetsClient(json_path=None, json_blob=json.dumps({"type": "service_account"}), spreadsheet_name="Book", worksheet_name="Leads")
    sc.append_lead(["a", "b"])  # worksheet created on first access
    # A second append to ensure calls work
    sc.append_lead(["c", "d"])

    ws = dummy_client.sheet.by_title["Leads"]
    assert ws.rows[-2] == ["a", "b"]
    assert ws.rows[-1] == ["c", "d"]


