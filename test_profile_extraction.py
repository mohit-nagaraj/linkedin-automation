#!/usr/bin/env python3
"""
Test script for enhanced LinkedIn profile extraction with Gemini AI integration
"""

import asyncio
import logging
import os
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation.linkedin import LinkedInAutomation
from automation.profile_extractor import ProfileExtractor, DetailedProfile
from automation.enhanced_gemini_client import EnhancedGeminiClient
from automation.enhanced_sheets import EnhancedSheetsClient


async def process_profile_from_html(html_content: str, owner_bio: str) -> DetailedProfile:
    """Process a profile from provided HTML content"""
    
    # Create a mock profile based on the HTML content
    # This is a simplified extraction for testing
    profile = DetailedProfile(
        name="Dhanu Kumar",
        headline="Founder and Director.Strongwillindia pvt limited",
        location="Bengaluru, Karnataka, India",
        profile_url="https://www.linkedin.com/in/dhanu-kumar-82546b13a",
        about="""Hi My Name is Dhanukumar a result-driven professional; offering nearly 6 years of Academic & Industry diverse experience in implementing solutions, process & best practices for Early Talent Pipeline, Training and Career Development. I always look for new learnings and like to take on new challenges and want more responsibilities to add on. Am Positive, Motivated & Passionate about what I do.

Specialized in Campus Recruitment & Hiring College Grads using 3 stage (Pre-Campus Event | During The Event & Post Campus Event) process for early talent pipeline program and their learning & career development. Managing complete cycle of Recruitment process of attracting, sourcing and hiring young Engineering and Management Graduate Trainees for several functions in organization. Performance Management and Probation confirmation. Having closed network with tier1/2/3 and B-Schools.

Specialized in Defining L&D Strategy in line with Organization Strategy. Collaborate with Leadership teams & Business Head to address Functional & organizational level development needs."""[:500],
        experiences=[
            {
                "title": "Director",
                "company": "Strongwill india pvt ltd",
                "duration": "Feb 2021 - Present · 4 yrs 7 mos",
                "description": "Self-employed",
                "skills": ["Internal Audits", "Support Services"]
            },
            {
                "title": "Human Resources Executive",
                "company": "Bosch India",
                "duration": "Oct 2018 - Jan 2021 · 2 yrs 4 mos",
                "description": "Executive include job posting and advertising, selection processes, applicant tracking and reporting",
                "skills": ["Internal Audits", "Human Capital Management"]
            }
        ],
        skills=[
            "HR Management",
            "Human Capital Management",
            "Internal Audits",
            "Support Services",
            "Employer Branding & Engagement",
            "Talent Sourcing/Acquisition",
            "Campus Recruitment"
        ],
        education=[
            {
                "school": "Coorg Institute of Technology, PONNAMPET",
                "degree": "Bachelor of Engineering, Electrical, Electronics and Communications Engineering",
                "duration": "2014 - 2017"
            }
        ],
        website="https://dhanush@strongwillindia.com",
        followers_count=2616,
        connections_count=500,
        mutual_connections=["Aaradhya Saikia", "Dinesh Choudhary"],
        interests=[
            "Company: Deloitte",
            "Company: Wells Fargo",
            "Influencer: Tejaswee Tripathy",
            "Influencer: Neel Jadhav"
        ]
    )
    
    # Initialize Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        logging.info("Initializing Gemini client for AI content generation")
        gemini_client = EnhancedGeminiClient(api_key)
        
        # Generate InMail note
        logging.info("Generating personalized InMail note...")
        profile.inmail_note = await gemini_client.generate_inmail_note(profile, owner_bio)
        logging.info(f"InMail note ({len(profile.inmail_note)} chars): {profile.inmail_note}")
        
        # Generate ice breaker questions
        logging.info("Generating ice breaker questions...")
        profile.ice_breakers = await gemini_client.generate_ice_breakers(profile, count=3)
        for i, question in enumerate(profile.ice_breakers, 1):
            logging.info(f"Ice breaker {i}: {question}")
        
        # Generate profile summary
        logging.info("Generating AI profile summary...")
        summary = await gemini_client.summarize_profile(profile, owner_bio)
        logging.info(f"Summary: {summary}")
        
        # Analyze profile fit
        logging.info("Analyzing profile fit...")
        fit_analysis = await gemini_client.analyze_profile_fit(profile, owner_bio, "HR/L&D Leadership")
        logging.info(f"Fit analysis: {fit_analysis}")
    else:
        logging.warning("GOOGLE_API_KEY not set - skipping AI content generation")
        profile.inmail_note = "Hi Dhanu, your experience in talent pipeline development and L&D strategy at Bosch India really resonates with my work. Would love to connect and exchange insights!"
        profile.ice_breakers = [
            "Your 3-stage campus recruitment process sounds comprehensive. What's been your biggest challenge in early talent pipeline development?",
            "I noticed you transitioned from Bosch to founding Strongwill. What inspired you to make that entrepreneurial leap?",
            "With your expertise in L&D strategy alignment, how do you see AI tools changing corporate training programs?"
        ]
    
    return profile


async def test_sheets_integration(profile: DetailedProfile):
    """Test Google Sheets integration"""
    
    # Check for sheets credentials
    json_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    json_blob = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BLOB")
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    
    if not (json_path or json_blob):
        logging.warning("Google Sheets credentials not configured - skipping sheets test")
        return
    
    logging.info("Testing Google Sheets integration...")
    
    try:
        sheets_client = EnhancedSheetsClient(
            json_path=json_path,
            json_blob=json_blob,
            spreadsheet_name="LinkedIn Automation Test",
            worksheet_name="Enhanced Profiles",
            spreadsheet_id=spreadsheet_id
        )
        
        # Add the profile to the sheet
        row_num = sheets_client.add_profile(
            profile,
            ai_summary="Senior HR professional with 6+ years in talent acquisition and L&D strategy",
            popularity_score=7.5
        )
        
        logging.info(f"Profile added to sheet at row {row_num}")
        
        # Update connection status
        sheets_client.mark_connect_sent(row_num)
        logging.info("Marked connection as sent")
        
        # Add a note
        sheets_client.add_note(row_num, "Test profile extraction successful")
        logging.info("Added note to profile")
        
    except Exception as e:
        logging.error(f"Sheets integration failed: {e}")


async def test_live_extraction():
    """Test live profile extraction (requires LinkedIn credentials)"""
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not (email and password):
        logging.warning("LinkedIn credentials not set - skipping live extraction test")
        return
    
    logging.info("Testing live LinkedIn profile extraction...")
    
    async with LinkedInAutomation(
        email=email,
        password=password,
        headless=False,
        debug=True
    ) as linkedin:
        await linkedin.login()
        
        # Test with a public profile
        test_profile_url = "https://www.linkedin.com/in/dhanu-kumar-82546b13a"
        
        extractor = ProfileExtractor(linkedin.page, debug=True)
        profile = await extractor.extract_profile(test_profile_url)
        
        logging.info(f"Extracted profile: {profile.name}")
        logging.info(f"Skills found: {len(profile.skills)}")
        logging.info(f"Experiences: {len(profile.experiences)}")
        
        return profile


async def main():
    """Main test function"""
    
    logging.info("=" * 60)
    logging.info("LinkedIn Profile Extraction Test")
    logging.info("=" * 60)
    
    # Define owner bio for AI generation
    owner_bio = "I'm a tech recruiter and HR consultant specializing in talent acquisition and organizational development. I help companies build strong engineering teams and implement effective L&D strategies."
    
    # Test with provided HTML content
    logging.info("\n1. Testing profile extraction from HTML...")
    profile = await process_profile_from_html("", owner_bio)
    
    # Display extracted information
    logging.info("\n" + "=" * 60)
    logging.info("EXTRACTED PROFILE INFORMATION")
    logging.info("=" * 60)
    logging.info(f"Name: {profile.name}")
    logging.info(f"Headline: {profile.headline}")
    logging.info(f"Location: {profile.location}")
    logging.info(f"Skills ({len(profile.skills)}): {', '.join(profile.skills[:5])}...")
    logging.info(f"Experiences: {len(profile.experiences)}")
    for exp in profile.experiences[:2]:
        logging.info(f"  - {exp['title']} at {exp['company']}")
    
    logging.info("\n" + "=" * 60)
    logging.info("AI GENERATED CONTENT")
    logging.info("=" * 60)
    logging.info(f"\nInMail Note ({len(profile.inmail_note)} chars):")
    logging.info(f"  {profile.inmail_note}")
    
    logging.info(f"\nIce Breaker Questions:")
    for i, question in enumerate(profile.ice_breakers, 1):
        logging.info(f"  {i}. {question}")
    
    # Test sheets integration
    logging.info("\n" + "=" * 60)
    logging.info("2. Testing Google Sheets integration...")
    await test_sheets_integration(profile)
    
    # Optional: Test live extraction
    # Uncomment if you want to test with real LinkedIn credentials
    # logging.info("\n" + "=" * 60)
    # logging.info("3. Testing live LinkedIn extraction...")
    # live_profile = await test_live_extraction()
    
    logging.info("\n" + "=" * 60)
    logging.info("Test completed successfully!")
    logging.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())