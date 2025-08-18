"""Unit test for duplicate profile prevention in EnhancedSheetsClient"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from automation.enhanced_sheets import EnhancedSheetsClient
from automation.profile_extractor import DetailedProfile


class TestDuplicatePrevention(unittest.TestCase):
    
    def create_test_profile(self, name: str, url: str) -> DetailedProfile:
        """Create a test profile with given name and URL"""
        profile = DetailedProfile(
            name=name,
            headline="Test Headline",
            location="Test Location", 
            profile_url=url,
            about="Test about section",
            experiences=[{"title": "Test Position", "company": "Test Company", "duration": "2 yrs"}],
            skills=["Python", "JavaScript"],
            education=[{"degree": "BS", "school": "Test University"}],
            certifications=["Cert1"],
            achievements=["Achievement1"],
            followers_count=100,
            connections_count=500,
            mutual_connections=["Mutual1"],
            recent_posts=["Recent post content"],
            interests=["Tech"],
            email="test@example.com",
            website="https://example.com",
            blogs=["https://blog.example.com"],
            social_links={"github": "https://github.com/test"},
            inmail_note="Test InMail",
            ice_breakers=["Question 1", "Question 2", "Question 3"]
        )
        return profile
    
    @patch('automation.enhanced_sheets.gspread')
    @patch('automation.enhanced_sheets.Credentials')
    def test_add_profile_prevents_duplicates(self, mock_creds, mock_gspread):
        """Test that add_profile updates existing profiles instead of creating duplicates"""
        
        # Setup mocks
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_gspread.authorize.return_value = mock_client
        mock_client.open.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        
        # Mock worksheet data with existing profile
        mock_worksheet.row_values.side_effect = [
            # First call returns headers
            EnhancedSheetsClient.COLUMNS,
            # Second call returns headers again for finding profile
            EnhancedSheetsClient.COLUMNS,
            # Third call returns existing row data
            ["2025-01-01", "Existing User", "Headline", "Location", 
             "https://www.linkedin.com/in/test-user", "", "", "", "", "", 
             "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", 
             "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        ]
        
        # Mock get_all_values to return existing data
        mock_worksheet.get_all_values.return_value = [
            EnhancedSheetsClient.COLUMNS,  # Headers
            ["2025-01-01", "Existing User", "Headline", "Location",
             "https://www.linkedin.com/in/test-user"] + [""] * (len(EnhancedSheetsClient.COLUMNS) - 5)
        ]
        
        # Create client
        client = EnhancedSheetsClient(
            json_path=None,
            json_blob='{"test": "creds"}',
            spreadsheet_name="Test Sheet",
            worksheet_name="Test"
        )
        
        # Create profiles with same URL
        profile_url = "https://www.linkedin.com/in/test-user"
        profile1 = self.create_test_profile("First Version", profile_url)
        profile2 = self.create_test_profile("Updated Version", profile_url)
        
        # Add first profile (should append)
        mock_worksheet.reset_mock()
        mock_worksheet.get_all_values.return_value = [
            EnhancedSheetsClient.COLUMNS  # Only headers, no data yet
        ]
        
        row1 = client.add_profile(profile1)
        
        # Verify append_row was called for first profile
        mock_worksheet.append_row.assert_called_once()
        self.assertEqual(row1, 1)  # First data row
        
        # Add duplicate profile (should update, not append)
        mock_worksheet.reset_mock()
        mock_worksheet.get_all_values.return_value = [
            EnhancedSheetsClient.COLUMNS,  # Headers
            ["2025-01-01", "First Version", "Test Headline", "Test Location",
             profile_url] + [""] * (len(EnhancedSheetsClient.COLUMNS) - 5)
        ]
        mock_worksheet.row_values.side_effect = [
            EnhancedSheetsClient.COLUMNS,  # Headers for update
            ["2025-01-01", "First Version", "Test Headline", "Test Location",
             profile_url] + [""] * (len(EnhancedSheetsClient.COLUMNS) - 5)  # Existing row data
        ]
        
        row2 = client.add_profile(profile2)
        
        # Verify update was called instead of append_row
        mock_worksheet.append_row.assert_not_called()
        mock_worksheet.update.assert_called_once()
        
        # Verify same row was returned
        self.assertEqual(row2, 2)  # Row 2 (after header)
        
        # Verify the update call had correct parameters
        update_call = mock_worksheet.update.call_args
        self.assertIn("A2:", update_call[0][0])  # Should update row 2
        
    @patch('automation.enhanced_sheets.gspread')
    @patch('automation.enhanced_sheets.Credentials')
    def test_find_profile_by_url(self, mock_creds, mock_gspread):
        """Test finding existing profiles by URL"""
        
        # Setup mocks
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_gspread.authorize.return_value = mock_client
        mock_client.open.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        
        # Mock worksheet data
        mock_worksheet.row_values.return_value = EnhancedSheetsClient.COLUMNS
        mock_worksheet.get_all_values.return_value = [
            EnhancedSheetsClient.COLUMNS,  # Headers
            ["2025-01-01", "User 1", "Headline 1", "Location 1",
             "https://www.linkedin.com/in/user1"] + [""] * (len(EnhancedSheetsClient.COLUMNS) - 5),
            ["2025-01-02", "User 2", "Headline 2", "Location 2", 
             "https://www.linkedin.com/in/user2"] + [""] * (len(EnhancedSheetsClient.COLUMNS) - 5),
            ["2025-01-03", "User 3", "Headline 3", "Location 3",
             "https://www.linkedin.com/in/user3"] + [""] * (len(EnhancedSheetsClient.COLUMNS) - 5)
        ]
        
        # Create client
        client = EnhancedSheetsClient(
            json_path=None,
            json_blob='{"test": "creds"}',
            spreadsheet_name="Test Sheet",
            worksheet_name="Test"
        )
        
        # Test finding existing profile
        row = client.find_profile_by_url("https://www.linkedin.com/in/user2")
        self.assertEqual(row, 3)  # Row 3 (header is row 1, user2 is row 3)
        
        # Test finding non-existent profile
        row = client.find_profile_by_url("https://www.linkedin.com/in/nonexistent")
        self.assertIsNone(row)
        
        # Test with empty sheet
        mock_worksheet.get_all_values.return_value = [EnhancedSheetsClient.COLUMNS]
        row = client.find_profile_by_url("https://www.linkedin.com/in/user1")
        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()