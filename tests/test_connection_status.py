import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from automation.linkedin import LinkedInAutomation, SearchResult


@pytest.mark.asyncio
async def test_connection_status_detection():
    """Test that the search_people method correctly identifies connection status."""
    
    # Create LinkedIn automation instance without using context manager
    linkedin = LinkedInAutomation(
        email="test@example.com",
        password="password",
        headless=True,
        debug=True
    )
    
    # Mock the page and browser
    linkedin.page = MagicMock()
    linkedin.browser = MagicMock()
    
    # Create proper mock objects for profile links
    profile_link1_first = MagicMock()
    profile_link1_first.count = AsyncMock(return_value=1)
    profile_link1_first.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/connected-user")
    
    profile_link2_first = MagicMock()
    profile_link2_first.count = AsyncMock(return_value=1)
    profile_link2_first.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/unconnected-user")
    
    profile_link3_first = MagicMock()
    profile_link3_first.count = AsyncMock(return_value=1)
    profile_link3_first.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/follow-user")
    
    # Create profile link locators that return .first objects
    profile_link1 = MagicMock()
    profile_link1.first = profile_link1_first
    
    profile_link2 = MagicMock()
    profile_link2.first = profile_link2_first
    
    profile_link3 = MagicMock()
    profile_link3.first = profile_link3_first
    
    # Create button mocks with .first
    button1_first = MagicMock()
    button1_first.count = AsyncMock(return_value=1)
    button1_first.text_content = AsyncMock(return_value="Message")
    button1_first.get_attribute = AsyncMock(return_value=None)
    
    button2_first = MagicMock()
    button2_first.count = AsyncMock(return_value=1)
    button2_first.text_content = AsyncMock(return_value="Connect")
    button2_first.get_attribute = AsyncMock(return_value=None)
    
    button3_first = MagicMock()
    button3_first.count = AsyncMock(return_value=1)
    button3_first.text_content = AsyncMock(return_value="Follow")
    button3_first.get_attribute = AsyncMock(return_value=None)
    
    button1 = MagicMock()
    button1.first = button1_first
    
    button2 = MagicMock()
    button2.first = button2_first
    
    button3 = MagicMock()
    button3.first = button3_first
    
    # Create name element mocks
    name_elem1_first = MagicMock()
    name_elem1_first.count = AsyncMock(return_value=1)
    name_elem1_first.text_content = AsyncMock(return_value="Connected User")
    
    name_elem2_first = MagicMock()
    name_elem2_first.count = AsyncMock(return_value=1)
    name_elem2_first.text_content = AsyncMock(return_value="Unconnected User")
    
    name_elem3_first = MagicMock()
    name_elem3_first.count = AsyncMock(return_value=1)
    name_elem3_first.text_content = AsyncMock(return_value="Follow User")
    
    name_elem1 = MagicMock()
    name_elem1.first = name_elem1_first
    
    name_elem2 = MagicMock()
    name_elem2.first = name_elem2_first
    
    name_elem3 = MagicMock()
    name_elem3.first = name_elem3_first
    
    # Create result containers
    result1 = MagicMock()
    result2 = MagicMock()
    result3 = MagicMock()
    
    # Setup locator side effects for each result
    def result1_locator(selector):
        if "a[href*='/in/']" in selector:
            return profile_link1
        elif "button" in selector:
            return button1
        elif "span[aria-hidden='true']" in selector:
            return name_elem1
        mock_obj = MagicMock()
        mock_obj.first = MagicMock()
        mock_obj.first.count = AsyncMock(return_value=0)
        return mock_obj
    
    def result2_locator(selector):
        if "a[href*='/in/']" in selector:
            return profile_link2
        elif "button" in selector:
            return button2
        elif "span[aria-hidden='true']" in selector:
            return name_elem2
        mock_obj = MagicMock()
        mock_obj.first = MagicMock()
        mock_obj.first.count = AsyncMock(return_value=0)
        return mock_obj
    
    def result3_locator(selector):
        if "a[href*='/in/']" in selector:
            return profile_link3
        elif "button" in selector:
            return button3
        elif "span[aria-hidden='true']" in selector:
            return name_elem3
        mock_obj = MagicMock()
        mock_obj.first = MagicMock()
        mock_obj.first.count = AsyncMock(return_value=0)
        return mock_obj
    
    result1.locator = result1_locator
    result2.locator = result2_locator
    result3.locator = result3_locator
    
    # Mock page methods
    search_results_locator = MagicMock()
    search_results_locator.all = AsyncMock(return_value=[result1, result2, result3])
    
    linkedin.page.locator = MagicMock(return_value=search_results_locator)
    linkedin.page.goto = AsyncMock()
    linkedin.page.evaluate = AsyncMock()
    
    # Mock _build_search_url and _human_pause
    linkedin._build_search_url = MagicMock(return_value="https://linkedin.com/search")
    linkedin._human_pause = AsyncMock()
    
    # Run search_people
    results = await linkedin.search_people(["test"], [], max_results=10)
    
    # Verify results - should have filtered out the "Message" button profile
    profile_urls = [r.profile_url for r in results]
    assert len(results) == 2  # Should only include unconnected profiles
    assert "https://www.linkedin.com/in/unconnected-user" in profile_urls
    assert "https://www.linkedin.com/in/follow-user" in profile_urls
    assert "https://www.linkedin.com/in/connected-user" not in profile_urls  # Connected profile should be filtered out
    
    # Verify names were extracted
    names = [r.name for r in results]
    assert "Unconnected User" in names
    assert "Follow User" in names


@pytest.mark.asyncio
async def test_fallback_when_no_containers():
    """Test fallback behavior when search result containers are not found."""
    
    linkedin = LinkedInAutomation(
        email="test@example.com",
        password="password",
        headless=True
    )
    
    # Mock the page
    linkedin.page = MagicMock()
    
    # Mock empty search results
    search_results_locator = MagicMock()
    search_results_locator.all = AsyncMock(return_value=[])
    
    linkedin.page.locator = MagicMock(return_value=search_results_locator)
    linkedin.page.goto = AsyncMock()
    linkedin.page.evaluate = AsyncMock(return_value=[])  # Return empty list for fallback
    
    # Mock _build_search_url and _human_pause
    linkedin._build_search_url = MagicMock(return_value="https://linkedin.com/search")
    linkedin._human_pause = AsyncMock()
    
    # Run search_people
    results = await linkedin.search_people(["test"], [], max_results=10)
    
    # Should return empty list when no results found
    assert len(results) == 0


def test_search_result_dataclass():
    """Test the SearchResult dataclass."""
    result = SearchResult(
        name="John Doe",
        headline="Software Engineer",
        location="San Francisco",
        profile_url="https://www.linkedin.com/in/johndoe",
        connection_status="not_connected"
    )
    
    assert result.name == "John Doe"
    assert result.headline == "Software Engineer"
    assert result.location == "San Francisco"
    assert result.profile_url == "https://www.linkedin.com/in/johndoe"
    assert result.connection_status == "not_connected"