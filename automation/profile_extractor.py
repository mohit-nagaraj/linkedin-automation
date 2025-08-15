from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import logging
import re
from playwright.async_api import Page


@dataclass
class DetailedProfile:
    """Comprehensive LinkedIn profile data structure"""
    # Basic Information
    name: str
    headline: str
    location: Optional[str] = None
    profile_url: str = ""
    about: Optional[str] = None
    
    # Experience and Skills
    experiences: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    
    # Education
    education: List[Dict[str, Any]] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    # Social and Contact
    email: Optional[str] = None
    website: Optional[str] = None
    blogs: List[str] = field(default_factory=list)
    social_links: Dict[str, str] = field(default_factory=dict)
    
    # Networking
    followers_count: Optional[int] = None
    connections_count: Optional[int] = None
    mutual_connections: List[str] = field(default_factory=list)
    
    # Content and Activity
    recent_posts: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    
    # AI Generated Content
    inmail_note: Optional[str] = None
    ice_breakers: List[str] = field(default_factory=list)


class ProfileExtractor:
    """Enhanced LinkedIn profile extractor with comprehensive data extraction"""
    
    def __init__(self, page: Page, debug: bool = False):
        self.page = page
        self.debug = debug
    
    async def extract_profile(self, profile_url: str) -> DetailedProfile:
        """Extract comprehensive profile information from LinkedIn"""
        if self.debug:
            logging.info(f"Extracting detailed profile: {profile_url}")
        
        # Navigate to profile
        await self.page.goto(profile_url, wait_until="domcontentloaded")
        await self.page.wait_for_selector("h1", state="visible", timeout=10000)
        
        # Initialize profile with basic info
        profile = DetailedProfile(
            name=await self._extract_name(),
            headline=await self._extract_headline(),
            location=await self._extract_location(),
            profile_url=profile_url,
            about=await self._extract_about()
        )
        
        # Extract comprehensive information
        profile.experiences = await self._extract_experiences()
        profile.skills = await self._extract_skills()
        profile.achievements = await self._extract_achievements()
        profile.education = await self._extract_education()
        profile.certifications = await self._extract_certifications()
        
        # Extract contact and social information
        contact_info = await self._extract_contact_info()
        profile.email = contact_info.get("email")
        profile.website = contact_info.get("website")
        profile.blogs = contact_info.get("blogs", [])
        profile.social_links = contact_info.get("social_links", {})
        
        # Extract networking information
        profile.followers_count = await self._extract_followers_count()
        profile.connections_count = await self._extract_connections_count()
        profile.mutual_connections = await self._extract_mutual_connections()
        
        # Extract activity and interests
        profile.recent_posts = await self._extract_recent_posts()
        profile.interests = await self._extract_interests()
        
        if self.debug:
            logging.info(f"Extracted profile data for: {profile.name}")
            logging.info(f"Skills: {len(profile.skills)}, Experiences: {len(profile.experiences)}")
        
        return profile
    
    async def _extract_name(self) -> str:
        """Extract profile name"""
        try:
            name_elem = await self.page.locator("h1").first.text_content()
            return name_elem.strip() if name_elem else ""
        except Exception as e:
            if self.debug:
                logging.warning(f"Failed to extract name: {e}")
            return ""
    
    async def _extract_headline(self) -> str:
        """Extract profile headline"""
        try:
            headline_elem = await self.page.locator("div.text-body-medium.break-words").first.text_content()
            return headline_elem.strip() if headline_elem else ""
        except Exception:
            return ""
    
    async def _extract_location(self) -> Optional[str]:
        """Extract profile location"""
        try:
            location_elem = await self.page.locator("span.text-body-small.inline.t-black--light.break-words").first.text_content()
            return location_elem.strip() if location_elem else None
        except Exception:
            return None
    
    async def _extract_about(self) -> Optional[str]:
        """Extract about section"""
        try:
            about_section = self.page.locator("section:has(#about)")
            if await about_section.count() > 0:
                about_text = await about_section.locator("div.display-flex.full-width").first.text_content()
                if about_text:
                    return about_text.strip()
        except Exception:
            pass
        return None
    
    async def _extract_experiences(self) -> List[Dict[str, Any]]:
        """Extract detailed work experience"""
        experiences = []
        try:
            exp_section = self.page.locator("section:has(#experience)")
            if await exp_section.count() > 0:
                exp_items = await exp_section.locator("li.artdeco-list__item").all()
                
                for item in exp_items:
                    try:
                        # Extract title, company, duration, description
                        title_elem = item.locator("div.display-flex.align-items-center span[aria-hidden='true']").first
                        company_elem = item.locator("span.t-14.t-normal span[aria-hidden='true']").first
                        duration_elem = item.locator("span.t-14.t-normal.t-black--light span[aria-hidden='true']").first
                        desc_elem = item.locator("div.display-flex.full-width").last
                        
                        exp_data = {
                            "title": await title_elem.text_content() if await title_elem.count() > 0 else "",
                            "company": await company_elem.text_content() if await company_elem.count() > 0 else "",
                            "duration": await duration_elem.text_content() if await duration_elem.count() > 0 else "",
                            "description": await desc_elem.text_content() if await desc_elem.count() > 0 else "",
                            "skills": []
                        }
                        
                        # Extract skills associated with this experience
                        skills_elem = item.locator("strong")
                        if await skills_elem.count() > 0:
                            skills_text = await skills_elem.text_content()
                            if skills_text and "skills" in skills_text.lower():
                                exp_data["skills"] = [s.strip() for s in skills_text.split(",")]
                        
                        if exp_data["title"] or exp_data["company"]:
                            experiences.append(exp_data)
                    except Exception as e:
                        if self.debug:
                            logging.warning(f"Failed to extract experience item: {e}")
                        continue
        except Exception as e:
            if self.debug:
                logging.warning(f"Failed to extract experiences: {e}")
        
        return experiences
    
    async def _extract_skills(self) -> List[str]:
        """Extract all skills from profile"""
        skills = []
        try:
            # Try main skills section
            skill_section = self.page.locator("section:has(#skills)")
            if await skill_section.count() > 0:
                skill_items = await skill_section.locator("div.mr1.hoverable-link-text.t-bold span[aria-hidden='true']").all()
                for item in skill_items:
                    text = await item.text_content()
                    if text and text.strip():
                        skills.append(text.strip())
            
            # Also extract skills from experience sections
            exp_skills = await self.page.locator("div strong:has-text('skills')").all()
            for skill_elem in exp_skills:
                parent = skill_elem.locator("..")
                text = await parent.text_content()
                if text:
                    # Parse skills from text like "Internal Audits, Support Services and +3 skills"
                    skill_parts = text.split(",")
                    for part in skill_parts:
                        clean_skill = part.strip()
                        if clean_skill and not clean_skill.startswith("+") and "skill" not in clean_skill.lower():
                            skills.append(clean_skill)
        except Exception as e:
            if self.debug:
                logging.warning(f"Failed to extract skills: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            if skill not in seen:
                seen.add(skill)
                unique_skills.append(skill)
        
        return unique_skills
    
    async def _extract_achievements(self) -> List[str]:
        """Extract achievements and honors"""
        achievements = []
        try:
            # Look for honors & awards section
            honors_section = self.page.locator("section:has(h2:has-text('Honors'))")
            if await honors_section.count() > 0:
                items = await honors_section.locator("li").all()
                for item in items:
                    text = await item.text_content()
                    if text:
                        achievements.append(text.strip())
            
            # Look for accomplishments
            accomplishments = self.page.locator("section:has(h2:has-text('Accomplishments'))")
            if await accomplishments.count() > 0:
                items = await accomplishments.locator("li").all()
                for item in items:
                    text = await item.text_content()
                    if text:
                        achievements.append(text.strip())
        except Exception:
            pass
        
        return achievements
    
    async def _extract_education(self) -> List[Dict[str, Any]]:
        """Extract education information"""
        education = []
        try:
            edu_section = self.page.locator("section:has(#education)")
            if await edu_section.count() > 0:
                edu_items = await edu_section.locator("li.artdeco-list__item").all()
                
                for item in edu_items:
                    try:
                        school_elem = item.locator("div.mr1.hoverable-link-text.t-bold span[aria-hidden='true']").first
                        degree_elem = item.locator("span.t-14.t-normal span[aria-hidden='true']").first
                        duration_elem = item.locator("span.t-14.t-normal.t-black--light span[aria-hidden='true']").first
                        
                        edu_data = {
                            "school": await school_elem.text_content() if await school_elem.count() > 0 else "",
                            "degree": await degree_elem.text_content() if await degree_elem.count() > 0 else "",
                            "duration": await duration_elem.text_content() if await duration_elem.count() > 0 else ""
                        }
                        
                        if edu_data["school"]:
                            education.append(edu_data)
                    except Exception:
                        continue
        except Exception:
            pass
        
        return education
    
    async def _extract_certifications(self) -> List[str]:
        """Extract certifications"""
        certifications = []
        try:
            cert_section = self.page.locator("section:has(h2:has-text('Licenses & certifications'))")
            if await cert_section.count() > 0:
                cert_items = await cert_section.locator("li").all()
                for item in cert_items:
                    title_elem = item.locator("span[aria-hidden='true']").first
                    if await title_elem.count() > 0:
                        text = await title_elem.text_content()
                        if text:
                            certifications.append(text.strip())
        except Exception:
            pass
        
        return certifications
    
    async def _extract_contact_info(self) -> Dict[str, Any]:
        """Extract contact information and social links"""
        contact_info = {
            "email": None,
            "website": None,
            "blogs": [],
            "social_links": {}
        }
        
        try:
            # Check for website in the main profile section
            website_elem = self.page.locator("section.pv-top-card--website a")
            if await website_elem.count() > 0:
                href = await website_elem.get_attribute("href")
                text = await website_elem.text_content()
                if href:
                    contact_info["website"] = href
                    # Check if it's a blog
                    if text and any(word in text.lower() for word in ["blog", "medium", "substack", "wordpress"]):
                        contact_info["blogs"].append(href)
                    # Check if it's an email
                    elif text and "@" in text:
                        contact_info["email"] = text.strip()
            
            # Try to access contact info overlay (may require connection)
            try:
                contact_button = self.page.locator("a#top-card-text-details-contact-info")
                if await contact_button.count() > 0:
                    await contact_button.click()
                    await self.page.wait_for_selector("section.pv-contact-info", timeout=3000)
                    
                    # Extract email
                    email_elem = self.page.locator("section.pv-contact-info a[href^='mailto:']")
                    if await email_elem.count() > 0:
                        email = await email_elem.text_content()
                        if email:
                            contact_info["email"] = email.strip()
                    
                    # Extract websites
                    website_elems = await self.page.locator("section.pv-contact-info a[href^='http']").all()
                    for elem in website_elems:
                        href = await elem.get_attribute("href")
                        if href:
                            # Categorize links
                            if any(domain in href.lower() for domain in ["github.com", "gitlab.com"]):
                                contact_info["social_links"]["github"] = href
                            elif "twitter.com" in href.lower() or "x.com" in href.lower():
                                contact_info["social_links"]["twitter"] = href
                            elif any(blog in href.lower() for blog in ["blog", "medium.com", "substack.com"]):
                                contact_info["blogs"].append(href)
                            else:
                                contact_info["website"] = href
                    
                    # Close the modal
                    close_button = self.page.locator("button[aria-label='Dismiss']")
                    if await close_button.count() > 0:
                        await close_button.click()
            except Exception:
                pass
        except Exception as e:
            if self.debug:
                logging.warning(f"Failed to extract contact info: {e}")
        
        return contact_info
    
    async def _extract_followers_count(self) -> Optional[int]:
        """Extract follower count"""
        try:
            # Try multiple selectors
            selectors = [
                "span:has-text('followers')",
                "p.pvs-header__optional-link:has-text('followers')",
                "span.t-bold:has-text('followers')"
            ]
            
            for selector in selectors:
                elem = self.page.locator(selector).first
                if await elem.count() > 0:
                    text = await elem.text_content()
                    if text:
                        # Extract number from text like "2,616 followers"
                        numbers = re.findall(r'[\d,]+', text)
                        if numbers:
                            return int(numbers[0].replace(',', ''))
        except Exception:
            pass
        
        return None
    
    async def _extract_connections_count(self) -> Optional[int]:
        """Extract connection count"""
        try:
            conn_elem = self.page.locator("span.t-bold:has-text('connections')").first
            if await conn_elem.count() > 0:
                text = await conn_elem.text_content()
                if text:
                    # Handle "500+ connections"
                    if "500+" in text:
                        return 500
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return int(numbers[0])
        except Exception:
            pass
        
        return None
    
    async def _extract_mutual_connections(self) -> List[str]:
        """Extract mutual connections"""
        mutual = []
        try:
            mutual_elem = self.page.locator("a.inline-flex span.t-normal")
            if await mutual_elem.count() > 0:
                text = await mutual_elem.text_content()
                if text and "mutual connection" in text.lower():
                    # Extract names from text like "John Doe, Jane Smith, and 7 other mutual connections"
                    names = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+)', text)
                    mutual.extend(names[:10])  # Limit to first 10 names
        except Exception:
            pass
        
        return mutual
    
    async def _extract_recent_posts(self) -> List[str]:
        """Extract recent post snippets from activity section"""
        posts = []
        try:
            # Look for activity/posts section
            activity_section = self.page.locator("section:has(#content_collections)")
            if await activity_section.count() > 0:
                # Get post text snippets
                post_items = await activity_section.locator("div.update-components-text span[dir='ltr']").all()
                for item in post_items[:3]:  # Get first 3 posts
                    text = await item.text_content()
                    if text:
                        # Truncate long posts
                        post_text = text.strip()[:200]
                        if len(text) > 200:
                            post_text += "..."
                        posts.append(post_text)
        except Exception:
            pass
        
        return posts
    
    async def _extract_interests(self) -> List[str]:
        """Extract interests (companies, influencers, groups followed)"""
        interests = []
        try:
            interests_section = self.page.locator("section:has(#interests)")
            if await interests_section.count() > 0:
                # Get company interests
                companies = await interests_section.locator("div[data-field='active_tab_companies_interests'] span[aria-hidden='true']").all()
                for company in companies[:5]:
                    text = await company.text_content()
                    if text and "follower" not in text.lower():
                        interests.append(f"Company: {text.strip()}")
                
                # Get influencer interests
                influencers = await interests_section.locator("div[data-field='active_tab_influencers_interests'] div.mr1.hoverable-link-text").all()
                for influencer in influencers[:5]:
                    text = await influencer.text_content()
                    if text:
                        interests.append(f"Influencer: {text.strip()}")
        except Exception:
            pass
        
        return interests