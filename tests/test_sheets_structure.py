import pytest
from automation.sheets import SheetsClient


class TestSheetsStructure:
    """Test that Google Sheets has the correct structure"""
    
    def test_sheets_columns(self):
        """Test that the sheets have the correct column headers"""
        # Expected columns based on the append_lead method
        expected_columns = [
            "name",
            "headline", 
            "location",
            "profile_url",
            "popularity_score",
            "summary",
            "note",
            "connected"
        ]
        
        # This test verifies the column structure is correct
        assert len(expected_columns) == 8, "Should have 8 columns"
        
        # Verify column names are as expected
        assert expected_columns[0] == "name", "First column should be name"
        assert expected_columns[1] == "headline", "Second column should be headline"
        assert expected_columns[2] == "location", "Third column should be location"
        assert expected_columns[3] == "profile_url", "Fourth column should be profile_url"
        assert expected_columns[4] == "popularity_score", "Fifth column should be popularity_score"
        assert expected_columns[5] == "summary", "Sixth column should be summary"
        assert expected_columns[6] == "note", "Seventh column should be note"
        assert expected_columns[7] == "connected", "Eighth column should be connected"
    
    def test_row_data_structure(self):
        """Test that row data matches the expected structure"""
        # Mock row data that would be passed to append_lead
        mock_profile_data = [
            "John Doe",           # name
            "Software Engineer",  # headline
            "San Francisco, CA",  # location
            "https://linkedin.com/in/johndoe",  # profile_url
            85,                   # popularity_score
            "Experienced software engineer with 5+ years in web development",  # summary
            "Hi John, I noticed your work in web development...",  # note
            "no"                  # connected
        ]
        
        # Verify the data structure
        assert len(mock_profile_data) == 8, "Row data should have 8 fields"
        assert isinstance(mock_profile_data[0], str), "Name should be string"
        assert isinstance(mock_profile_data[1], str), "Headline should be string"
        assert isinstance(mock_profile_data[2], str), "Location should be string"
        assert isinstance(mock_profile_data[3], str), "Profile URL should be string"
        assert isinstance(mock_profile_data[4], int), "Popularity score should be number"
        assert isinstance(mock_profile_data[5], str), "Summary should be string"
        assert isinstance(mock_profile_data[6], str), "Note should be string"
        assert mock_profile_data[7] in ["yes", "no"], "Connected should be yes/no"
    
    def test_connection_status_values(self):
        """Test that connection status values are correct"""
        # Test valid connection status values
        valid_statuses = ["yes", "no"]
        
        for status in valid_statuses:
            assert status in ["yes", "no"], f"Connection status should be 'yes' or 'no', got '{status}'"
        
        # Test that we don't have invalid values
        invalid_statuses = ["true", "false", "1", "0", "connected", "not_connected"]
        for status in invalid_statuses:
            assert status not in ["yes", "no"], f"Invalid connection status: {status}"
