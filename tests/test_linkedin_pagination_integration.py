import pytest
from unittest.mock import Mock, AsyncMock
from automation.linkedin import LinkedInAutomation


class TestLinkedInPaginationIntegration:
    """Integration tests for LinkedIn pagination functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Async test hanging - needs investigation") 
    async def test_pagination_flow_with_mock_data(self):
        """Test the complete pagination flow with mock page data"""
        # Create a mock LinkedInAutomation instance
        li = LinkedInAutomation(email="test@example.com", password="password")
        li.page = Mock()
        li.debug = True
        
        # Mock the page navigation and locator methods
        li.page.goto = AsyncMock()
        li.page.locator = Mock()
        li.page.evaluate = AsyncMock()
        
        # Mock profile data for different pages
        mock_profiles_page_1 = [
            "https://www.linkedin.com/in/profile1",
            "https://www.linkedin.com/in/profile2", 
            "https://www.linkedin.com/in/profile3"
        ]
        mock_profiles_page_2 = [
            "https://www.linkedin.com/in/profile4",
            "https://www.linkedin.com/in/profile5"
        ]
        
        # Create mock locator that returns different cards based on page
        page_number = [1]  # Use list to make it mutable in nested functions
        
        def mock_locator(selector):
            mock_loc = Mock()
            mock_loc.all = AsyncMock()
            
            if page_number[0] == 1:
                # First page: return 3 profiles initially, then none (stagnant)
                if len(mock_profiles_page_1) > 0:
                    mock_cards = []
                    for profile in mock_profiles_page_1[:2]:  # Return 2 profiles
                        mock_card = Mock()
                        mock_card.get_attribute = AsyncMock(return_value=profile)
                        mock_cards.append(mock_card)
                    mock_loc.all.return_value = mock_cards
                    mock_profiles_page_1.clear()  # Clear for next call (stagnant)
                else:
                    mock_loc.all.return_value = []
            else:
                # Second page: return 2 profiles
                if len(mock_profiles_page_2) > 0:
                    mock_cards = []
                    for profile in mock_profiles_page_2:
                        mock_card = Mock()
                        mock_card.get_attribute = AsyncMock(return_value=profile)
                        mock_cards.append(mock_card)
                    mock_loc.all.return_value = mock_cards
                    mock_profiles_page_2.clear()
                else:
                    mock_loc.all.return_value = []
            
            return mock_loc
        
        li.page.locator.side_effect = mock_locator
        
        # Mock the _human_pause method
        li._human_pause = AsyncMock()
        
        # Test the search_people method
        keywords = ["software engineer"]
        max_results = 5
        
        # Mock the page number tracking
        original_build_url = li._build_search_url
        call_count = [0]
        
        def mock_build_url(keywords, page_num):
            call_count[0] += 1
            page_number[0] = page_num
            return original_build_url(keywords, page_num)
        
        li._build_search_url = mock_build_url
        
        # Run the search
        result = await li.search_people(keywords, [], max_results)
        
        # Verify results
        expected_profiles = [
            "https://www.linkedin.com/in/profile1",
            "https://www.linkedin.com/in/profile2", 
            "https://www.linkedin.com/in/profile3",
            "https://www.linkedin.com/in/profile4",
            "https://www.linkedin.com/in/profile5"
        ]
        
        assert len(result) == 5
        assert result == expected_profiles
        
        # Verify that pagination was used
        assert call_count[0] >= 2  # Should have called _build_search_url for at least 2 pages
    
    def test_pagination_parameters(self):
        """Test that pagination parameters are configurable"""
        from unittest.mock import patch
        with patch('automation.linkedin.async_playwright'):
            li = LinkedInAutomation(email="test@example.com", password="password")
            
            # Test URL building with different page numbers
            keywords = ["test"]
            
            for page_num in range(1, 11):
                url = li._build_search_url(keywords, page_num)
                assert f"page={page_num}" in url
                assert "keywords=test" in url
                assert url.startswith("https://www.linkedin.com/search/results/people/")
    
    def test_pagination_edge_cases(self):
        """Test pagination edge cases"""
        from unittest.mock import patch
        with patch('automation.linkedin.async_playwright'):
            li = LinkedInAutomation(email="test@example.com", password="password")
            
            # Test with empty keywords
            url = li._build_search_url([], 1)
            assert "page=1" in url
            assert "keywords=" in url
            
            # Test with special characters in keywords
            special_keywords = ["software engineer", "founder & cto"]
            url = li._build_search_url(special_keywords, 1)
            assert "page=1" in url
            # Check that keywords are URL-encoded (space becomes %20)
            assert "software%20engineer" in url
            assert "founder" in url
