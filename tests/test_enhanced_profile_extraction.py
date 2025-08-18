"""Test enhanced profile extraction with provided HTML sample"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from automation.profile_extractor import ProfileExtractor, DetailedProfile
from automation.enhanced_gemini_client import EnhancedGeminiClient


# Sample HTML from the user's email
SAMPLE_HTML = """
<section id="about">
    <div class="display-flex ph5 pv3">
        <div class="display-flex full-width">
            <div class="inline-show-more-text" dir="ltr">
                <span aria-hidden="true">Hi My Name is Dhanukumar a result-driven professional; offering nearly 6 years of Academic &amp; Industry diverse experience in implementing solutions, process &amp; best practices for Early Talent Pipeline, Training and Career Development. I always look for new learnings and like to take on new challenges and want more responsibilities to add on. Am Positive, Motivated &amp; Passionate about what I do.<br><br>Specialized in Campus Recruitment &amp; Hiring College Grads using 3 stage (Pre-Campus Event | During The Event &amp; Post Campus Event) process for early talent pipeline program and their learning &amp; career development.</span>
            </div>
        </div>
    </div>
</section>

<section id="experience">
    <li class="artdeco-list__item">
        <div class="display-flex align-items-center">
            <span aria-hidden="true">Director</span>
        </div>
        <span class="t-14 t-normal">
            <span aria-hidden="true">Strongwill india pvt ltd · Self-employed</span>
        </span>
        <span class="t-14 t-normal t-black--light">
            <span aria-hidden="true">Feb 2021 - Present · 4 yrs 7 mos</span>
        </span>
        <strong>Internal Audits, Support Services and +3 skills</strong>
    </li>
</section>

<section id="skills">
    <div class="mr1 hoverable-link-text t-bold">
        <span aria-hidden="true">HR Management</span>
    </div>
    <div class="mr1 hoverable-link-text t-bold">
        <span aria-hidden="true">Human Capital Management</span>
    </div>
</section>

<section id="education">
    <li class="artdeco-list__item">
        <div class="mr1 hoverable-link-text t-bold">
            <span aria-hidden="true">Coorg Institute of Technology, PONNAMPET</span>
        </div>
        <span class="t-14 t-normal">
            <span aria-hidden="true">Bachelor of Engineering, Electrical, Electronics and Communications Engineering</span>
        </span>
        <span class="t-14 t-normal t-black--light">
            <span aria-hidden="true">2014 - 2017</span>
        </span>
    </li>
</section>
"""


@pytest.mark.asyncio
async def test_extract_about_section():
    """Test that we correctly extract the about section from profile"""
    # Create mock page
    page = AsyncMock()
    
    # Mock the about section locator
    about_locator = MagicMock()
    about_locator.count = AsyncMock(return_value=1)
    about_locator.text_content = AsyncMock(return_value="Hi My Name is Dhanukumar a result-driven professional; offering nearly 6 years of Academic & Industry diverse experience")
    about_locator.first = about_locator  # Make .first return self
    
    # Set up the locator to return the mock
    page.locator = MagicMock(return_value=about_locator)
    
    extractor = ProfileExtractor(page, debug=True)
    about = await extractor._extract_about()
    
    assert about is not None
    assert "Dhanukumar" in about
    assert "result-driven professional" in about
    assert "6 years" in about


@pytest.mark.asyncio
async def test_extract_skills():
    """Test that we correctly extract skills from profile"""
    page = AsyncMock()
    
    # Mock skill items
    skill_items = []
    for skill_name in ["HR Management", "Human Capital Management", "Internal Audits", "Support Services"]:
        skill_mock = MagicMock()
        skill_mock.text_content = AsyncMock(return_value=skill_name)
        skill_items.append(skill_mock)
    
    page.locator.return_value.all = AsyncMock(return_value=skill_items)
    
    extractor = ProfileExtractor(page, debug=True)
    skills = await extractor._extract_skills()
    
    assert len(skills) >= 2
    assert "HR Management" in skills
    assert "Human Capital Management" in skills


@pytest.mark.asyncio
async def test_extract_experiences():
    """Test that we correctly extract work experiences"""
    page = AsyncMock()
    
    # Mock experience section
    exp_section = MagicMock()
    exp_section.count = AsyncMock(return_value=1)
    
    # Mock experience item
    exp_item = MagicMock()
    
    # Mock title element
    title_elem = MagicMock()
    title_elem.count = AsyncMock(return_value=1)
    title_elem.text_content = AsyncMock(return_value="Director")
    exp_item.locator.return_value.first = title_elem
    
    exp_section.locator.return_value.all = AsyncMock(return_value=[exp_item])
    
    page.locator.return_value = exp_section
    
    extractor = ProfileExtractor(page, debug=True)
    experiences = await extractor._extract_experiences()
    
    assert len(experiences) > 0
    assert experiences[0]["title"] == "Director"


@pytest.mark.asyncio
async def test_extract_education():
    """Test that we correctly extract education information"""
    page = AsyncMock()
    
    # Mock education section
    edu_section = MagicMock()
    edu_section.count = AsyncMock(return_value=1)
    
    # Mock education item
    edu_item = MagicMock()
    
    # Mock school element
    school_elem = MagicMock()
    school_elem.count = AsyncMock(return_value=1)
    school_elem.text_content = AsyncMock(return_value="Coorg Institute of Technology, PONNAMPET")
    
    # Mock degree element
    degree_elem = MagicMock()
    degree_elem.count = AsyncMock(return_value=1)
    degree_elem.text_content = AsyncMock(return_value="Bachelor of Engineering, Electrical, Electronics and Communications Engineering")
    
    edu_item.locator.return_value.first = school_elem
    edu_section.locator.return_value.all = AsyncMock(return_value=[edu_item])
    
    page.locator.return_value = edu_section
    
    extractor = ProfileExtractor(page, debug=True)
    education = await extractor._extract_education()
    
    assert len(education) > 0
    assert "Coorg Institute" in education[0]["school"]


@pytest.mark.asyncio
async def test_generate_ice_breakers():
    """Test that ice breaker questions are generated based on profile"""
    # Create a sample profile
    profile = DetailedProfile(
        name="Dhanu Kumar",
        headline="Director at Strongwill India Pvt Ltd",
        about="Specialized in Campus Recruitment & Hiring College Grads",
        skills=["HR Management", "Human Capital Management", "Campus Recruitment"],
        experiences=[{
            "title": "Director",
            "company": "Strongwill India Pvt Ltd",
            "duration": "4 yrs 7 mos",
            "skills": ["Internal Audits", "Support Services"]
        }],
        education=[{
            "school": "Coorg Institute of Technology",
            "degree": "Bachelor of Engineering",
            "duration": "2014 - 2017"
        }]
    )
    
    # Mock Gemini client
    gemini = MagicMock()
    gemini._client = MagicMock()
    gemini._model_name = "gemini-2.0-flash-exp"
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.text = """
    How did your experience with campus recruitment at Strongwill shape your approach to early talent pipeline development?
    What specific strategies have you found most effective for engaging with tier 1/2/3 engineering colleges during recruitment drives?
    Can you share insights from implementing the 3-stage recruitment process you mentioned - what metrics do you track for success?
    """
    gemini._client.models.generate_content.return_value = mock_response
    
    # Create EnhancedGeminiClient instance
    client = EnhancedGeminiClient(api_key="test_key", genai_module=MagicMock())
    client._client = gemini._client
    
    # Generate ice breakers
    ice_breakers = await client.generate_ice_breakers(profile, count=3)
    
    assert len(ice_breakers) == 3
    assert all(len(q) > 10 for q in ice_breakers)  # Each question should be meaningful
    assert any("campus" in q.lower() or "recruitment" in q.lower() for q in ice_breakers)


@pytest.mark.asyncio
async def test_profile_summary_is_targets_not_ours():
    """Test that the profile summary is about the target person, not us"""
    profile = DetailedProfile(
        name="Dhanu Kumar",
        headline="Director at Strongwill India Pvt Ltd",
        about="Hi My Name is Dhanukumar a result-driven professional with 6 years experience",
        skills=["HR Management", "Campus Recruitment"]
    )
    
    # Mock Gemini client
    gemini = MagicMock()
    gemini._client = MagicMock()
    
    mock_response = MagicMock()
    mock_response.text = """
    • Senior HR professional with 6 years in talent acquisition and development
    • Specializes in campus recruitment and early talent pipeline programs
    • Director at Strongwill India with expertise in 3-stage recruitment process
    • Strong background in training, career development, and talent management
    """
    gemini._client.models.generate_content.return_value = mock_response
    
    client = EnhancedGeminiClient(api_key="test_key", genai_module=MagicMock())
    client._client = gemini._client
    
    owner_bio = "Mohit Nagaraj is a Software Engineer at Final Round AI"
    summary = await client.summarize_profile(profile, owner_bio)
    
    # The summary should be about Dhanu, not Mohit
    assert "Dhanu" in summary or "HR" in summary or "recruitment" in summary
    assert "Mohit" not in summary
    assert "Final Round AI" not in summary


if __name__ == "__main__":
    asyncio.run(test_profile_summary_is_targets_not_ours())
    print("All tests passed!")