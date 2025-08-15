from __future__ import annotations

import asyncio
from typing import List

from dotenv import load_dotenv
from .config import load_settings
from .linkedin import LinkedInAutomation
from .gemini_client import GeminiClient
from .scoring import compute_popularity_score
from .sheets import SheetsClient
from .logging_config import configure_logging
import logging


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
    configure_logging(logging.DEBUG if settings.debug else logging.INFO, use_rich=True, rich_tracebacks=True)

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
        use_persistent_context=settings.use_persistent_context,
        user_data_dir=settings.user_data_dir,
        browser_channel=settings.browser_channel,
        debug=settings.debug,
        min_action_delay_ms=settings.min_action_delay_ms,
        max_action_delay_ms=settings.max_action_delay_ms,
    ) as li:
        logging.info("Starting LinkedIn login")
        await li.login()
        logging.info("Login step complete. Proceeding to people search.")
        profile_urls = await li.search_people(settings.search_keywords, settings.locations, max_results=settings.max_profiles)
        logging.info("Found %d profiles", len(profile_urls))

        processed_count = 0
        logging.info("Starting to process %d profiles (MAX_PROFILES=%d)", len(profile_urls), settings.max_profiles)
        
        for url in profile_urls:
            logging.info("Processing profile %d/%d: %s", processed_count + 1, settings.max_profiles, url)
            
            profile = await li.scrape_profile(url)
            popularity = compute_popularity_score(profile, settings.seniority_keywords)
            summary = await gemini.summarize_profile(profile, OWNER_BIO)
            note = await gemini.craft_connect_note(profile, OWNER_BIO)

            connected = False
            try:
                connected = await li.connect_with_note(url, note)
            except Exception as e:
                logging.warning("Failed to connect with %s: %s", url, str(e))
                connected = False

            if sheets:
                row_data = [
                    profile.name,
                    profile.headline,
                    profile.location or "",
                    profile.profile_url,
                    popularity,
                    summary,
                    note,
                    "yes" if connected else "no",
                ]
                sheets.append_lead(row_data)
                logging.info("Added to Google Sheets: %s (%s)", profile.name, "Connected" if connected else "Not Connected")
            
            processed_count += 1
            
            # Check if we've reached MAX_PROFILES
            if processed_count >= settings.max_profiles:
                logging.info("Reached MAX_PROFILES (%d), stopping processing", settings.max_profiles)
                if sheets:
                    logging.info("Google Sheets updated with %d profiles", processed_count)
                break
        
        logging.info("Finished processing %d profiles", processed_count)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()


