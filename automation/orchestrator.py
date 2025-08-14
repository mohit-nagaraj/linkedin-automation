from __future__ import annotations

import asyncio
from typing import List

from dotenv import load_dotenv
from .config import load_settings
from .linkedin import LinkedInAutomation
from .gemini_client import GeminiClient
from .scoring import compute_popularity_score
from .sheets import SheetsClient


OWNER_BIO = (
    "Mohit Nagaraj is a Computer Science and Engineering student (CGPA 9.23) with strong expertise in "
    "JavaScript, TypeScript, Go, and Dart, alongside frameworks and tools like React, Next.js, Node.js, "
    "PostgreSQL, MongoDB, Flutter, Redis, and AWS. He has developed projects like Solace, VidStreamX, "
    "TrendAi, and Exsense. Professionally, he worked at Boho/SellerSetu and Springreen (APIs, microservices, CI/CD). "
    "Hackathon winner and OSS contributor (KubeVirt)."
)


async def run() -> None:
    load_dotenv()
    settings = load_settings()

    if not settings.linkedin_email or not settings.linkedin_password:
        raise RuntimeError("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables.")
    if not settings.search_keywords:
        raise RuntimeError("Set SEARCH_KEYWORDS env var (comma-separated).")

    sheets: SheetsClient | None = None
    if settings.gsheet_name:
        sheets = SheetsClient(
            json_path=settings.gcp_service_account_json_path,
            json_blob=settings.gcp_service_account_json,
            spreadsheet_name=settings.gsheet_name,
            worksheet_name=settings.gsheet_worksheet,
            oauth_client_secrets_path=settings.oauth_client_secrets_path,
            oauth_token_path=settings.oauth_token_path,
            spreadsheet_id=settings.gsheet_id,
        )

    gemini = GeminiClient(api_key=settings.google_api_key, model_name="gemini-1.5-flash")

    async with LinkedInAutomation(
        email=settings.linkedin_email,
        password=settings.linkedin_password,
        headless=settings.headless,
        slow_mo_ms=settings.slow_mo_ms,
        navigation_timeout_ms=settings.navigation_timeout_ms,
        storage_state_path=settings.storage_state_path,
    ) as li:
        await li.login()
        profile_urls = await li.search_people(settings.search_keywords, settings.locations, max_results=settings.max_profiles)

        for url in profile_urls:
            profile = await li.scrape_profile(url)
            popularity = compute_popularity_score(profile, settings.seniority_keywords)
            summary = await gemini.summarize_profile(profile, OWNER_BIO)
            note = await gemini.craft_connect_note(profile, OWNER_BIO)

            connected = False
            try:
                connected = await li.connect_with_note(url, note)
            except Exception:
                connected = False

            if sheets:
                sheets.append_lead([
                    profile.name,
                    profile.headline,
                    profile.location or "",
                    profile.profile_url,
                    popularity,
                    summary,
                    note,
                    "yes" if connected else "no",
                ])


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()


