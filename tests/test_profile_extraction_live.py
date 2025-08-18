#!/usr/bin/env python3
"""
Test script to verify profile extraction and ice breaker generation
This test uses mocks and doesn't require actual API credentials
"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
from automation.profile_extractor import DetailedProfile
from automation.enhanced_gemini_client import EnhancedGeminiClient

# Sample profile data based on the HTML provided
SAMPLE_PROFILE = DetailedProfile(
    name="Dhanu Kumar",
    headline="Founder and Director at Strongwill India Pvt Limited",
    location="Bengaluru, Karnataka, India",
    profile_url="https://www.linkedin.com/in/dhanu-kumar-82546b13a",
    about=(
        "Hi My Name is Dhanukumar a result-driven professional; offering nearly 6 years of Academic & "
        "Industry diverse experience in implementing solutions, process & best practices for Early Talent "
        "Pipeline, Training and Career Development. I always look for new learnings and like to take on "
        "new challenges and want more responsibilities to add on. Am Positive, Motivated & Passionate about what I do.\n\n"
        "Specialized in Campus Recruitment & Hiring College Grads using 3 stage (Pre-Campus Event | During The Event "
        "& Post Campus Event) process for early talent pipeline program and their learning & career development."
    ),
    experiences=[
        {
            "title": "Director",
            "company": "Strongwill india pvt ltd",
            "duration": "Feb 2021 - Present · 4 yrs 7 mos",
            "description": "",
            "skills": ["Internal Audits", "Support Services"]
        },
        {
            "title": "Human Resources Executive",
            "company": "Bosch India",
            "duration": "Oct 2018 - Jan 2021 · 2 yrs 4 mos",
            "description": "Executive include job posting and advertising, selection processes, applicant tracking",
            "skills": ["Internal Audits", "Human Capital Management"]
        }
    ],
    skills=[
        "HR Management",
        "Human Capital Management",
        "Internal Audits",
        "Support Services",
    ],
    education=[
        {
            "degree": "Bachelor's degree",
            "school": "Bangalore University",
            "year": "2013 - 2016"
        }
    ],
    certifications=[],
    achievements=[],
    followers_count=1234,
    connections_count=500,
    mutual_connections=[],
    recent_posts=[],
    interests=[],
    email=None,
    website=None,
    blogs=[],
    social_links={},
    inmail_note=None,
    ice_breakers=[]
)


class TestProfileExtractionMocked:
    """Tests for profile extraction using mocked responses"""
    
    def test_profile_data_structure(self):
        """Test that DetailedProfile correctly holds all the data"""
        assert SAMPLE_PROFILE.name == "Dhanu Kumar"
        assert "Founder and Director" in SAMPLE_PROFILE.headline
        assert len(SAMPLE_PROFILE.experiences) == 2
        assert len(SAMPLE_PROFILE.skills) >= 4
        assert "Bosch India" in SAMPLE_PROFILE.experiences[1]["company"]
        assert SAMPLE_PROFILE.followers_count == 1234
        assert len(SAMPLE_PROFILE.education) == 1
    
    @pytest.mark.asyncio
    async def test_ice_breaker_generation(self):
        """Test generating ice breaker questions"""
        # Create mock genai module
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "You mentioned implementing a 3-stage campus recruitment process - what specific metrics did you find most valuable for measuring early talent pipeline success?\n"
            "Having worked with both Bosch and now leading Strongwill India, how has your approach to talent development evolved between corporate and entrepreneurial environments?\n"
            "Your focus on early talent pipeline programs is impressive - what's been your most successful strategy for retaining and developing college graduates in their first year?"
        )
        
        # Setup the mock chain properly
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response
        
        client = EnhancedGeminiClient(api_key="test_key", genai_module=mock_genai)
        questions = await client.generate_ice_breakers(SAMPLE_PROFILE, count=3)
        
        assert len(questions) == 3
        assert all(len(q) > 20 for q in questions)
        assert any("campus recruitment" in q.lower() or "talent" in q.lower() for q in questions)
    
    @pytest.mark.asyncio
    async def test_profile_summary(self):
        """Test generating profile summary that focuses on target person"""
        # Create mock genai module
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "• HR Leader & Entrepreneur: Founder/Director at Strongwill India with 6+ years in talent acquisition\n"
            "• Campus Recruitment Expert: Specialized in 3-stage early talent pipeline processes\n"
            "• Corporate Experience: Former HR Executive at Bosch India (2+ years)\n"
            "• Talent Development Focus: Passionate about early career development and learning programs\n"
            "• Skills: Human Capital Management, Internal Audits, Support Services"
        )
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response
        
        owner_bio = "Mohit Nagaraj is a Software Engineer at Final Round AI"
        
        client = EnhancedGeminiClient(api_key="test_key", genai_module=mock_genai)
        summary = await client.summarize_profile(SAMPLE_PROFILE, owner_bio)
        
        assert len(summary) > 50
        assert "•" in summary  # Should have bullet points
        assert "HR" in summary or "talent" in summary.lower()
    
    @pytest.mark.asyncio
    async def test_inmail_generation(self):
        """Test generating personalized InMail note"""
        # Create mock genai module
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "Hi Dhanu, impressed by your 6 years building talent pipelines at Strongwill & Bosch. "
            "Your 3-stage campus recruitment process aligns with our talent strategy at Final Round AI. "
            "Would love to exchange insights on early talent development. Open to connect?"
        )
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response
        
        owner_bio = "Mohit Nagaraj is a Software Engineer at Final Round AI"
        
        client = EnhancedGeminiClient(api_key="test_key", genai_module=mock_genai)
        inmail = await client.generate_inmail_note(SAMPLE_PROFILE, owner_bio)
        
        assert len(inmail) <= 300
        assert "Dhanu" in inmail
        assert len(inmail) > 50  # Should have meaningful content


@pytest.mark.integration 
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="Requires GEMINI_API_KEY environment variable")
class TestProfileExtractionLiveAPI:
    """Live tests that require actual Gemini API credentials"""
    
    @pytest.mark.asyncio
    async def test_live_ice_breaker_generation(self):
        """Test ice breaker generation with actual API"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        import google.generativeai as genai
        client = EnhancedGeminiClient(api_key=api_key, genai_module=genai)
        
        questions = await client.generate_ice_breakers(SAMPLE_PROFILE, count=3)
        assert len(questions) == 3
        assert all(len(q) > 20 for q in questions)
    
    @pytest.mark.asyncio
    async def test_live_profile_summary(self):
        """Test profile summary with actual API"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        import google.generativeai as genai
        client = EnhancedGeminiClient(api_key=api_key, genai_module=genai)
        
        owner_bio = "Mohit Nagaraj is a Software Engineer at Final Round AI"
        summary = await client.summarize_profile(SAMPLE_PROFILE, owner_bio)
        
        assert len(summary) > 50
        assert "•" in summary or "-" in summary  # Should have bullet points or dashes
    
    @pytest.mark.asyncio
    async def test_live_inmail_generation(self):
        """Test InMail generation with actual API"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        import google.generativeai as genai
        client = EnhancedGeminiClient(api_key=api_key, genai_module=genai)
        
        owner_bio = "Mohit Nagaraj is a Software Engineer at Final Round AI"
        inmail = await client.generate_inmail_note(SAMPLE_PROFILE, owner_bio)
        
        assert len(inmail) <= 300
        assert "Dhanu" in inmail or "Kumar" in inmail  # Should mention the person's name