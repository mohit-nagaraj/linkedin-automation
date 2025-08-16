"""Test Google Sheets row-wise update functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from automation.sheets import SheetsClient


class TestSheetsUpdates:
    """Test suite for Google Sheets incremental updates."""

    @pytest.fixture
    def mock_gspread(self):
        """Create a mock gspread client."""
        with patch('automation.sheets.gspread') as mock:
            # Setup mock worksheet
            mock_worksheet = MagicMock()
            mock_worksheet.row_values.return_value = [
                "name", "headline", "location", "profile_url", 
                "popularity_score", "summary", "note", "connected"
            ]
            mock_worksheet.get_all_values.return_value = [
                ["name", "headline", "location", "profile_url", "popularity_score", "summary", "note", "connected"],
                ["John Doe", "Engineer", "NYC", "url1", "5", "", "", "pending"]
            ]
            
            # Setup mock spreadsheet
            mock_spreadsheet = MagicMock()
            mock_spreadsheet.worksheet.return_value = mock_worksheet
            
            # Setup mock client
            mock_client = MagicMock()
            mock_client.open.return_value = mock_spreadsheet
            mock.authorize.return_value = mock_client
            
            yield mock, mock_worksheet

    @patch('automation.sheets._service_account_creds')
    def test_append_lead_returns_row_number(self, mock_creds, mock_gspread):
        """Test that append_lead returns the correct row number."""
        mock_gspread_module, mock_worksheet = mock_gspread
        mock_creds.return_value = MagicMock()
        
        client = SheetsClient(
            json_path=None,
            json_blob="{}",
            spreadsheet_name="test",
            worksheet_name="sheet1"
        )
        
        # Test appending a row
        row_data = ["Jane Smith", "CTO", "SF", "url2", "8", "", "", "pending"]
        row_num = client.append_lead(row_data)
        
        # Should return row 3 (after header and existing row)
        assert row_num == 2
        # append_lead pads to 16 columns
        padded_row = row_data + [''] * (16 - len(row_data))
        mock_worksheet.append_row.assert_called_once_with(padded_row, value_input_option="RAW")

    @patch('automation.sheets._service_account_creds')
    def test_update_cell(self, mock_creds, mock_gspread):
        """Test updating a single cell."""
        mock_gspread_module, mock_worksheet = mock_gspread
        mock_creds.return_value = MagicMock()
        
        client = SheetsClient(
            json_path=None,
            json_blob="{}",
            spreadsheet_name="test",
            worksheet_name="sheet1"
        )
        
        # Test updating summary cell
        client.update_cell(2, "summary", "This is a test summary")
        
        # Verify batch_update was called with correct parameters
        mock_worksheet.batch_update.assert_called_once()
        call_args = mock_worksheet.batch_update.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]['range'] == 'F2'  # F is column 6 (summary)
        assert call_args[0]['values'] == [["This is a test summary"]]

    @patch('automation.sheets._service_account_creds')
    def test_update_row_multiple_columns(self, mock_creds, mock_gspread):
        """Test updating multiple columns in a row."""
        mock_gspread_module, mock_worksheet = mock_gspread
        mock_creds.return_value = MagicMock()
        
        client = SheetsClient(
            json_path=None,
            json_blob="{}",
            spreadsheet_name="test",
            worksheet_name="sheet1"
        )
        
        # Test updating multiple columns
        updates = {
            "summary": "Profile summary here",
            "note": "Connection note here",
            "connected": "yes"
        }
        client.update_row(2, updates)
        
        # Verify batch_update was called
        mock_worksheet.batch_update.assert_called_once()
        call_args = mock_worksheet.batch_update.call_args[0][0]
        
        # Should have 3 updates
        assert len(call_args) == 3
        
        # Check that all expected columns are updated
        ranges = {item['range'] for item in call_args}
        assert 'F2' in ranges  # summary column
        assert 'G2' in ranges  # note column
        assert 'H2' in ranges  # connected column

    @patch('automation.sheets._service_account_creds')
    def test_col_num_to_letter(self, mock_creds, mock_gspread):
        """Test column number to letter conversion."""
        mock_gspread_module, mock_worksheet = mock_gspread
        mock_creds.return_value = MagicMock()
        
        client = SheetsClient(
            json_path=None,
            json_blob="{}",
            spreadsheet_name="test",
            worksheet_name="sheet1"
        )
        
        # Test various column conversions
        assert client._col_num_to_letter(1) == "A"
        assert client._col_num_to_letter(26) == "Z"
        assert client._col_num_to_letter(27) == "AA"
        assert client._col_num_to_letter(52) == "AZ"
        assert client._col_num_to_letter(53) == "BA"
        assert client._col_num_to_letter(702) == "ZZ"
        assert client._col_num_to_letter(703) == "AAA"

    @patch('automation.sheets._service_account_creds')
    def test_update_nonexistent_column(self, mock_creds, mock_gspread):
        """Test that updating a non-existent column is handled gracefully."""
        mock_gspread_module, mock_worksheet = mock_gspread
        mock_creds.return_value = MagicMock()
        
        client = SheetsClient(
            json_path=None,
            json_blob="{}",
            spreadsheet_name="test",
            worksheet_name="sheet1"
        )
        
        # Try to update a column that doesn't exist
        client.update_cell(2, "nonexistent_column", "value")
        
        # batch_update should not be called since column doesn't exist
        mock_worksheet.batch_update.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])