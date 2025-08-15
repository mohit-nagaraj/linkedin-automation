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
    if settings.gsheet_name or settings.gsheet_id:
        logging.info("Initializing Google Sheets client...")
        logging.debug("GSHEET_NAME: %s", settings.gsheet_name)
        logging.debug("GSHEET_ID: %s", settings.gsheet_id)
        logging.debug("GCP_SERVICE_ACCOUNT_JSON_PATH: %s", settings.gcp_service_account_json_path)
        try:
            sheets = SheetsClient(
                json_path=settings.gcp_service_account_json_path,
                json_blob=settings.gcp_service_account_json,
                spreadsheet_name=settings.gsheet_name,
                worksheet_name=settings.gsheet_worksheet,
                oauth_client_secrets_path=settings.oauth_client_secrets_path,
                oauth_token_path=settings.oauth_token_path,
                spreadsheet_id=settings.gsheet_id,
            )
            logging.info("Google Sheets client initialized successfully")
        except Exception as e:
            logging.error("Failed to initialize Google Sheets client: %s", str(e))
            sheets = None
    else:
        logging.warning("Google Sheets not configured - GSHEET_NAME or GSHEET_ID not set")

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
        search_results = await li.search_people(settings.search_keywords, settings.locations, max_results=settings.max_profiles)
        logging.info("Found %d profiles", len(search_results))

        # Step 1: Save all search results to Google Sheets first
        row_mapping = {}  # Map profile URLs to row numbers
        if sheets:
            logging.info("Saving search results to Google Sheets...")
            for idx, result in enumerate(search_results, 1):
                initial_row_data = [
                    result.name or "Unknown",
                    result.headline or "",
                    result.location or "",
                    result.profile_url,
                    0,  # popularity score (to be filled later)
                    "",  # summary (to be filled later)
                    "",  # note (to be filled later)
                    result.connection_status,  # connection status from search
                ]
                row_num = sheets.append_lead(initial_row_data)
                row_mapping[result.profile_url] = row_num
                logging.debug("Added search result %d/%d to row %d: %s", idx, len(search_results), row_num, result.name or "Unknown")
            logging.info("Saved %d search results to Google Sheets", len(search_results))

        # Step 2: Process each profile for detailed scraping
        processed_count = 0
        logging.info("Starting to process %d profiles (MAX_PROFILES=%d)", len(search_results), settings.max_profiles)
        
        for result in search_results:
            url = result.profile_url
            row_num = row_mapping.get(url) if sheets else None
            
            logging.info("Processing profile %d/%d: %s", processed_count + 1, settings.max_profiles, url)
            
            # Scrape full profile details
            profile = await li.scrape_profile(url)
            popularity = compute_popularity_score(profile, settings.seniority_keywords)
            
            # Update the row with scraped profile data
            if sheets and row_num:
                updates = {
                    "name": profile.name,  # Update with accurate name from profile
                    "headline": profile.headline,
                    "location": profile.location or "",
                    "popularity_score": popularity,
                }
                sheets.update_row(row_num, updates)
                logging.debug("Updated profile data for row %d: %s", row_num, profile.name)
            
            # Generate summary and update
            summary = await gemini.summarize_profile(profile, OWNER_BIO)
            if sheets and row_num:
                sheets.update_cell(row_num, "summary", summary)
                logging.debug("Updated summary for row %d", row_num)
            
            # Generate connection note and update
            note = await gemini.craft_connect_note(profile, OWNER_BIO)
            if sheets and row_num:
                sheets.update_cell(row_num, "note", note)
                logging.debug("Updated note for row %d", row_num)

            # Try to connect (only if not already connected)
            if result.connection_status != "connected":
                connected = False
                try:
                    connected = await li.connect_with_note(url, note)
                except Exception as e:
                    logging.warning("Failed to connect with %s: %s", url, str(e))
                    connected = False
                
                if sheets and row_num:
                    sheets.update_cell(row_num, "connected", "yes" if connected else "no")
                    logging.info("Updated connection status for %s: %s", profile.name, "Connected" if connected else "Not Connected")
            else:
                logging.info("Skipping connection for %s (already connected)", profile.name)
            
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


