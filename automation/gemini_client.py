from __future__ import annotations

from typing import Optional
import asyncio
import google.generativeai as genai

from .linkedin import Profile


class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name)

    async def summarize_profile(self, profile: Profile, owner_bio: str) -> str:
        prompt = (
            "You are an expert technical recruiter and networker. Summarize the following LinkedIn profile in 4-6 bullet points: "
            "focus on seniority, notable work, tech stack, domain expertise, and signals of influence (talks, OSS, publications).\n\n"
            f"Owner bio (me): {owner_bio}\n"
            f"Name: {profile.name}\n"
            f"Headline: {profile.headline}\n"
            f"Location: {profile.location or 'N/A'}\n"
            f"About: {profile.about or 'N/A'}\n"
            f"Experiences: {', '.join(profile.experiences) if profile.experiences else 'N/A'}\n"
            f"Skills: {', '.join(profile.skills) if profile.skills else 'N/A'}\n"
            f"Followers: {profile.followers_count or 'N/A'}\n\n"
            "Return only the bullet list, concise and specific."
        )
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        text = response.text if hasattr(response, "text") else str(response)
        return text.strip()

    async def craft_connect_note(self, profile: Profile, owner_bio: str) -> str:
        prompt = (
            "Write a short, warm, and specific LinkedIn connection note (max 280 chars) that sounds human, not salesy.\n"
            "Include one concrete detail from their profile (project, role, domain, or skill).\n"
            "Avoid emojis. Use first name if available.\n\n"
            f"Owner bio (me): {owner_bio}\n"
            f"Name: {profile.name}\n"
            f"Headline: {profile.headline}\n"
            f"About: {profile.about or 'N/A'}\n"
            f"Top experiences: {', '.join(profile.experiences[:3]) if profile.experiences else 'N/A'}\n"
            f"Skills: {', '.join(profile.skills[:5]) if profile.skills else 'N/A'}\n\n"
            "Return only the final note, no preface."
        )
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        text = response.text if hasattr(response, "text") else str(response)
        return text.strip().replace("\n", " ")[:280]


