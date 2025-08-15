from __future__ import annotations

from typing import Optional, Any, List, Dict
import asyncio
import importlib
import logging

from .profile_extractor import DetailedProfile


class EnhancedGeminiClient:
    """Enhanced Gemini client with InMail and ice breaker generation"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp", genai_module: Any | None = None) -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini.")
        
        # Use google-genai SDK
        genai = genai_module or importlib.import_module("google.genai")
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name
    
    async def generate_inmail_note(self, profile: DetailedProfile, owner_bio: str) -> str:
        """Generate a personalized InMail note (max 300 characters)"""
        
        # Build a comprehensive profile context
        profile_context = self._build_profile_context(profile)
        
        prompt = f"""You are an expert networker writing a personalized InMail message.

Write a SHORT, WARM, and HIGHLY PERSONALIZED LinkedIn InMail note (MAXIMUM 300 characters) that:
1. References a SPECIFIC achievement, skill, or experience from their profile
2. Creates a connection between their experience and mine
3. Sounds genuine and human, not salesy or generic
4. Uses their first name
5. Ends with a soft call to action

My background: {owner_bio}

Their profile:
{profile_context}

IMPORTANT: The message must be UNDER 300 characters. Be concise but impactful.
Return ONLY the message text, no explanation."""

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model_name,
            contents=prompt,
        )
        
        text = response.text if hasattr(response, "text") else str(response)
        message = text.strip().replace("\n", " ")
        
        # Ensure it's under 300 characters
        if len(message) > 300:
            message = message[:297] + "..."
        
        logging.debug(f"Generated InMail for {profile.name}: {len(message)} chars")
        return message
    
    async def generate_ice_breakers(self, profile: DetailedProfile, count: int = 3) -> List[str]:
        """Generate ice breaker questions based on profile skills and experience"""
        
        profile_context = self._build_profile_context(profile)
        
        prompt = f"""You are an expert conversation starter analyzing this LinkedIn profile.

Generate {count} thoughtful, specific ice breaker questions that:
1. Reference SPECIFIC skills, projects, or experiences from their profile
2. Show genuine interest in their expertise
3. Are open-ended and encourage detailed responses
4. Demonstrate that you've actually read their profile
5. Are professional but friendly

Profile details:
{profile_context}

Generate exactly {count} questions. Each should be 1-2 sentences and reference different aspects of their profile.
Format: Return ONLY the questions, one per line, no numbering or bullets."""

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model_name,
            contents=prompt,
        )
        
        text = response.text if hasattr(response, "text") else str(response)
        
        # Parse the response into individual questions
        questions = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if line and not line[0].isdigit():  # Skip numbered lines
                # Clean up any leading symbols
                if line[0] in ['-', '*', '•']:
                    line = line[1:].strip()
                questions.append(line)
        
        # Ensure we have the requested number of questions
        questions = questions[:count]
        
        logging.debug(f"Generated {len(questions)} ice breakers for {profile.name}")
        return questions
    
    async def summarize_profile(self, profile: DetailedProfile, owner_bio: str) -> str:
        """Generate a comprehensive profile summary"""
        
        profile_context = self._build_profile_context(profile)
        
        prompt = f"""Summarize this LinkedIn profile in 4-6 bullet points focusing on:
- Seniority level and current role
- Key technical skills and expertise
- Notable achievements or projects
- Domain expertise and industry experience
- Potential fit with my background

My background: {owner_bio}

Profile:
{profile_context}

Return only bullet points, be specific and concise."""

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model_name,
            contents=prompt,
        )
        
        text = response.text if hasattr(response, "text") else str(response)
        logging.debug(f"Summarized profile for {profile.name}")
        return text.strip()
    
    async def analyze_profile_fit(self, profile: DetailedProfile, owner_bio: str, target_role: str = "") -> Dict[str, Any]:
        """Analyze how well a profile fits with owner's needs"""
        
        profile_context = self._build_profile_context(profile)
        
        prompt = f"""Analyze this LinkedIn profile for potential collaboration/networking fit.

My background: {owner_bio}
{"Target role/need: " + target_role if target_role else ""}

Profile:
{profile_context}

Provide a JSON response with:
{{
  "fit_score": <1-10>,
  "strengths": ["strength1", "strength2", ...],
  "common_ground": ["shared_skill_or_interest1", ...],
  "conversation_topics": ["topic1", "topic2", ...],
  "potential_value": "brief description of mutual value"
}}

Return ONLY valid JSON."""

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model_name,
            contents=prompt,
        )
        
        text = response.text if hasattr(response, "text") else str(response)
        
        # Parse JSON response
        import json
        try:
            result = json.loads(text.strip())
            logging.debug(f"Analyzed fit for {profile.name}: score {result.get('fit_score', 'N/A')}")
            return result
        except json.JSONDecodeError:
            logging.warning("Failed to parse fit analysis as JSON")
            return {
                "fit_score": 5,
                "strengths": [],
                "common_ground": [],
                "conversation_topics": [],
                "potential_value": "Analysis failed"
            }
    
    def _build_profile_context(self, profile: DetailedProfile) -> str:
        """Build a comprehensive context string from profile data"""
        
        context_parts = [
            f"Name: {profile.name}",
            f"Headline: {profile.headline}",
            f"Location: {profile.location or 'Not specified'}"
        ]
        
        if profile.about:
            # Truncate long about sections
            about_text = profile.about[:500] + "..." if len(profile.about) > 500 else profile.about
            context_parts.append(f"About: {about_text}")
        
        if profile.experiences:
            exp_texts = []
            for exp in profile.experiences[:3]:  # Top 3 experiences
                exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get('duration'):
                    exp_text += f" ({exp['duration']})"
                if exp.get('skills'):
                    exp_text += f" - Skills: {', '.join(exp['skills'][:3])}"
                exp_texts.append(exp_text)
            context_parts.append(f"Recent Experience: {'; '.join(exp_texts)}")
        
        if profile.skills:
            context_parts.append(f"Top Skills: {', '.join(profile.skills[:10])}")
        
        if profile.achievements:
            context_parts.append(f"Achievements: {', '.join(profile.achievements[:3])}")
        
        if profile.education:
            edu_texts = []
            for edu in profile.education[:2]:  # Top 2 education entries
                edu_text = f"{edu.get('degree', '')} from {edu.get('school', '')}"
                edu_texts.append(edu_text)
            context_parts.append(f"Education: {'; '.join(edu_texts)}")
        
        if profile.certifications:
            context_parts.append(f"Certifications: {', '.join(profile.certifications[:3])}")
        
        if profile.website or profile.blogs:
            links = []
            if profile.website:
                links.append(f"Website: {profile.website}")
            if profile.blogs:
                links.append(f"Blog: {profile.blogs[0]}")
            context_parts.append(' | '.join(links))
        
        if profile.followers_count:
            context_parts.append(f"Followers: {profile.followers_count:,}")
        
        if profile.recent_posts:
            context_parts.append(f"Recent post snippet: {profile.recent_posts[0][:100]}...")
        
        if profile.interests:
            context_parts.append(f"Interests: {', '.join(profile.interests[:5])}")
        
        return '\n'.join(context_parts)