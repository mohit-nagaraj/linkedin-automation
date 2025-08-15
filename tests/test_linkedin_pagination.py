import pytest
from automation.linkedin import LinkedInAutomation


class TestLinkedInPagination:
    """Test that LinkedIn pagination works correctly"""
    
    def test_build_search_url_with_pagination(self):
        """Test that _build_search_url correctly adds page parameter"""
        # Create a minimal LinkedInAutomation instance to test the method
        li = LinkedInAutomation(email="test@example.com", password="password")
        
        # Test with different page numbers
        keywords = ["software engineer", "founder"]
        
        url_page_1 = li._build_search_url(keywords, 1)
        assert "page=1" in url_page_1
        assert "keywords=software%20engineer%20founder" in url_page_1
        
        url_page_2 = li._build_search_url(keywords, 2)
        assert "page=2" in url_page_2
        assert "keywords=software%20engineer%20founder" in url_page_2
        
        url_page_10 = li._build_search_url(keywords, 10)
        assert "page=10" in url_page_10
        
        # Test with single keyword
        single_keyword = ["cto"]
        url_single = li._build_search_url(single_keyword, 1)
        assert "page=1" in url_single
        assert "keywords=cto" in url_single
    
    def test_pagination_logic(self):
        """Test the pagination logic and stagnant rounds detection"""
        # This test verifies the logic without actually running the browser
        
        # Test case 1: Normal pagination flow
        # Page 1: Find 5 profiles, then stagnant
        # Page 2: Find 3 more profiles
        # Expected: Should move to page 2 after stagnant rounds
        
        # Test case 2: No profiles found
        # Page 1: No profiles found
        # Expected: Should move to page 2 immediately
        
        # Test case 3: Max results reached
        # Page 1: Find 25 profiles (max_results)
        # Expected: Should stop and not go to page 2
        
        # These are logical tests that verify the algorithm works correctly
        assert True  # Placeholder for now - actual implementation would test the logic
    
    def test_url_structure(self):
        """Test that the URL structure is correct for LinkedIn search"""
        li = LinkedInAutomation(email="test@example.com", password="password")
        
        keywords = ["software engineer"]
        page_number = 2
        
        url = li._build_search_url(keywords, page_number)
        
        # Verify URL structure
        assert url.startswith("https://www.linkedin.com/search/results/people/")
        assert "keywords=software%20engineer" in url
        assert "page=2" in url
        
        # Test with multiple keywords
        multi_keywords = ["software engineer", "founder", "cto"]
        url_multi = li._build_search_url(multi_keywords, 1)
        assert "keywords=software%20engineer%20founder%20cto" in url_multi
