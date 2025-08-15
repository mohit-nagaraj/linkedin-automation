import pytest
from unittest.mock import AsyncMock, MagicMock
from automation.linkedin import LinkedInAutomation


@pytest.mark.asyncio
async def test_connection_status_detection():
    """Test that the search_people method correctly filters connected profiles."""
    
    # Create LinkedIn automation instance
    linkedin = LinkedInAutomation(
        email="test@example.com",
        password="password",
        headless=True,
        debug=True
    )
    
    # Mock the page and browser
    linkedin.page = MagicMock()
    linkedin.browser = MagicMock()
    
    # Mock search results HTML structure
    # Result 1: Connected profile (button says "Message")
    result1 = MagicMock()
    profile_link1 = MagicMock()
    profile_link1.count = AsyncMock(return_value=1)
    profile_link1.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/connected-user")
    result1.locator = MagicMock(side_effect=[
        profile_link1,  # First call for profile link
        MagicMock(  # Second call for button
            count=AsyncMock(return_value=1),
            text_content=AsyncMock(return_value="Message")
        )
    ])
    
    # Result 2: Not connected profile (button says "Connect")
    result2 = MagicMock()
    profile_link2 = MagicMock()
    profile_link2.count = AsyncMock(return_value=1)
    profile_link2.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/unconnected-user")
    button2 = MagicMock()
    button2.count = AsyncMock(return_value=1)
    button2.text_content = AsyncMock(return_value="Connect")
    
    def result2_locator(selector):
        if "a[href*='/in/']" in selector:
            return profile_link2
        elif "button" in selector:
            return button2
        return MagicMock(count=AsyncMock(return_value=0))
    
    result2.locator = MagicMock(side_effect=result2_locator)
    
    # Result 3: Not connected profile (button says "Follow")
    result3 = MagicMock()
    profile_link3 = MagicMock()
    profile_link3.count = AsyncMock(return_value=1)
    profile_link3.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/follow-user")
    button3 = MagicMock()
    button3.count = AsyncMock(return_value=1)
    button3.text_content = AsyncMock(return_value="Follow")
    
    def result3_locator(selector):
        if "a[href*='/in/']" in selector:
            return profile_link3
        elif "button" in selector:
            return button3
        return MagicMock(count=AsyncMock(return_value=0))
    
    result3.locator = MagicMock(side_effect=result3_locator)
    
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
    
    # Verify results
    assert len(results) == 2  # Should only include unconnected profiles
    assert "https://www.linkedin.com/in/unconnected-user" in results
    assert "https://www.linkedin.com/in/follow-user" in results
    assert "https://www.linkedin.com/in/connected-user" not in results  # Connected profile should be filtered out


@pytest.mark.asyncio
async def test_fallback_when_no_containers():
    """Test fallback behavior when search result containers are not found."""
    
    linkedin = LinkedInAutomation(
        email="test@example.com",
        password="password",
        headless=True,
        debug=True
    )
    
    linkedin.page = MagicMock()
    linkedin.browser = MagicMock()
    
    # Mock no search result containers found
    empty_locator = MagicMock()
    empty_locator.all = AsyncMock(return_value=[])
    
    # Mock fallback cards
    card1 = MagicMock()
    card1.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/user1")
    card2 = MagicMock()
    card2.get_attribute = AsyncMock(return_value="https://www.linkedin.com/in/user2")
    
    cards_locator = MagicMock()
    cards_locator.all = AsyncMock(return_value=[card1, card2])
    
    def page_locator(selector):
        if "div.ohQFMJgsahXYKwkqjYqSorBCVcblSnDIgFig" in selector:
            return empty_locator
        elif "a[href*='/in/']" in selector:
            return cards_locator
        return empty_locator
    
    linkedin.page.locator = MagicMock(side_effect=page_locator)
    linkedin.page.goto = AsyncMock()
    linkedin.page.evaluate = AsyncMock()
    linkedin._build_search_url = MagicMock(return_value="https://linkedin.com/search")
    linkedin._human_pause = AsyncMock()
    
    results = await linkedin.search_people(["test"], [], max_results=10)
    
    # In fallback mode, all profiles are added
    assert len(results) == 2
    assert "https://www.linkedin.com/in/user1" in results
    assert "https://www.linkedin.com/in/user2" in results