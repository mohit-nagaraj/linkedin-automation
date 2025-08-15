from __future__ import annotations

import asyncio
from typing import List
from datetime import datetime

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

    gemini = GeminiClient(api_key=settings.google_api_key, model_name="gemini-2.5-flash-preview-05-20")

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
                # Check if profile already exists
                existing_row = sheets.find_row_by_url(result.profile_url)
                
                if existing_row:
                    logging.info("Profile already exists at row %d: %s", existing_row, result.profile_url)
                    row_mapping[result.profile_url] = existing_row
                    # Update last updated timestamp
                    sheets.update_cell(existing_row, "Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    # Extract position from headline if available
                    position = ""
                    if result.headline:
                        # Common patterns: "Title at Company" or "Title | Company"
                        if " at " in result.headline:
                            position = result.headline.split(" at ")[0]
                        elif " | " in result.headline:
                            position = result.headline.split(" | ")[0]
                        else:
                            position = result.headline.split(",")[0] if "," in result.headline else ""
                    
                    initial_row_data = [
                        result.name or "Unknown",
                        position,  # Position extracted from headline
                        result.headline or "",
                        result.location or "",
                        result.profile_url,
                        0,  # popularity score (to be filled later)
                        "",  # summary (to be filled later)
                        "",  # note (to be filled later)
                        "no",  # connect_sent (will be updated after connection attempt)
                        result.connection_status or "",  # Connection status from search
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Date Added
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Last Updated
                        "",  # About (to be filled later)
                        "",  # Experience (to be filled later)
                        "",  # Education (to be filled later)
                        "",  # Skills (to be filled later)
                    ]
                    logging.info("Adding new profile - Row %d: Name=%s, Position=%s, Status=%s, URL=%s", 
                                idx, result.name or "Unknown", position, result.connection_status, result.profile_url)
                    logging.debug("Full row data: %s", initial_row_data)
                    row_num = sheets.append_lead(initial_row_data)
                    row_mapping[result.profile_url] = row_num
                    logging.debug("Added search result %d/%d to row %d: %s", idx, len(search_results), row_num, result.name or "Unknown")
            logging.info("Processed %d search results in Google Sheets", len(search_results))

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
                # Extract position from headline if available
                position = ""
                if profile.headline:
                    if " at " in profile.headline:
                        position = profile.headline.split(" at ")[0]
                    elif " | " in profile.headline:
                        position = profile.headline.split(" | ")[0]
                    else:
                        position = profile.headline.split(",")[0] if "," in profile.headline else ""
                
                # Format experience and skills for storage (education not available in current Profile)
                experience_str = "\n".join([f"• {exp}" for exp in (profile.experiences or [])])
                education_str = ""  # Education field not available in current profile structure
                skills_str = ", ".join(profile.skills or [])
                
                updates = {
                    "Name": profile.name,  # Update with accurate name from profile
                    "Position": position,
                    "Headline": profile.headline,
                    "Location": profile.location or "",
                    "Popularity Score": popularity,
                    "About": profile.about or "",
                    "Experience": experience_str,
                    "Education": education_str,
                    "Skills": skills_str,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                logging.info("Updating row %d with full profile data: Name=%s, Position=%s, Score=%d", 
                            row_num, profile.name, position, popularity)
                logging.debug("Profile update data: %s", updates)
                sheets.update_row(row_num, updates)
                logging.debug("Updated profile data for row %d: %s", row_num, profile.name)
            
            # Generate summary and update
            summary = await gemini.summarize_profile(profile, OWNER_BIO)
            if sheets and row_num:
                sheets.update_cell(row_num, "Summary", summary)
                logging.info("Updated summary for row %d: %s", row_num, summary[:100] + "..." if len(summary) > 100 else summary)
            
            # Generate connection note and update
            note = await gemini.craft_connect_note(profile, OWNER_BIO)
            if sheets and row_num:
                sheets.update_cell(row_num, "Connection Note", note)
                logging.info("Updated connection note for row %d: %s", row_num, note[:100] + "..." if len(note) > 100 else note)

            # Try to connect (only if not already connected)
            if result.connection_status != "connected":
                connect_sent = False
                try:
                    connect_sent = await li.connect_with_note(url, note)
                    if connect_sent:
                        logging.info("Successfully sent connection request to %s", profile.name)
                    else:
                        logging.info("Could not send connection request to %s (button not found or already pending)", profile.name)
                except Exception as e:
                    logging.warning("Failed to send connection request to %s: %s", profile.name, str(e))
                    connect_sent = False
                
                if sheets and row_num:
                    sheets.update_cell(row_num, "Connect Sent", "yes" if connect_sent else "no")
                    logging.info("Updated Connect Sent status for %s: %s", profile.name, "yes" if connect_sent else "no")
            else:
                logging.info("Skipping connection for %s (already connected)", profile.name)
                if sheets and row_num:
                    # Mark as already connected (connection was sent in the past and accepted)
                    sheets.update_cell(row_num, "Connect Sent", "yes")
                    sheets.update_cell(row_num, "Connection Status", "connected")
            
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


