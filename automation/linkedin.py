from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import asyncio
import random
import time
import logging
import re

from playwright.async_api import async_playwright, Browser, Page
import os


@dataclass
class Profile:
    name: str
    headline: str
    location: Optional[str]
    profile_url: str
    about: Optional[str]
    experiences: List[str]
    skills: List[str]
    followers_count: Optional[int]


@dataclass
class SearchResult:
    name: str
    headline: Optional[str]
    location: Optional[str]
    profile_url: str
    connection_status: str  # "connected", "not_connected", or "unknown"


class LinkedInAutomation:
    def __init__(self, email: str, password: str, headless: bool = False, slow_mo_ms: int = 0, navigation_timeout_ms: int = 30000, storage_state_path: str | None = None, use_persistent_context: bool = True, user_data_dir: str | None = None, browser_channel: str | None = None, debug: bool = False, min_action_delay_ms: int = 0, max_action_delay_ms: int = 0, test_mode: bool = True):
        self.email = email
        self.password = password
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms
        self.navigation_timeout_ms = navigation_timeout_ms
        self.storage_state_path = storage_state_path
        self.use_persistent_context = use_persistent_context
        self.user_data_dir = user_data_dir
        self.browser_channel = browser_channel
        self.debug = debug
        self.min_action_delay_ms = min_action_delay_ms
        self.max_action_delay_ms = max_action_delay_ms
        self.test_mode = test_mode
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self) -> "LinkedInAutomation":
        if self.debug:
            logging.info("Starting Playwright and launching browser (headless=%s, channel=%s)", self.headless, self.browser_channel)
        self.playwright = await async_playwright().start()
        launch_args = dict(channel=self.browser_channel) if self.browser_channel else {}
        if self.use_persistent_context and self.user_data_dir:
            if self.debug:
                logging.info("Using persistent profile at %s", self.user_data_dir)
            context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                slow_mo=self.slow_mo_ms,
                **launch_args,
            )
            self.browser = context.browser
        else:
            self.browser = await self.playwright.chromium.launch(headless=self.headless, slow_mo=self.slow_mo_ms, **launch_args)
            storage = None
            if self.storage_state_path and os.path.exists(self.storage_state_path):
                storage = self.storage_state_path
                if self.debug:
                    logging.info("Loading storage state from %s", self.storage_state_path)
            context = await self.browser.new_context(storage_state=storage)
        self.page = await context.new_page()
        self.page.set_default_timeout(self.navigation_timeout_ms)
        if self.debug:
            logging.info("Browser context ready (persistent=%s, user_data_dir=%s)", self.use_persistent_context, self.user_data_dir)
            self._attach_navigation_logging()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def login(self) -> None:
        assert self.page is not None
        if self.debug:
            logging.info("Navigating to feed")
        await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        if "login" in self.page.url:
            if self.debug:
                logging.info("Navigating to login")
            await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            await self.page.fill("input#username", self.email)
            await self.page.fill("input#password", self.password)
            await self.page.click("button[type=submit]")
            # Wait for stable state without hard-coding a selector that may change
            try:
                await self.page.wait_for_load_state("networkidle", timeout=self.navigation_timeout_ms)
            except Exception:
                pass
            # If still not on feed, allow a brief 2FA/checkpoint window, then proceed
            try:
                await self.page.wait_for_url("**/feed**", timeout=15000)
            except Exception:
                if self.debug:
                    logging.info("Not redirected to feed; continuing (possibly 2FA/captcha). Current URL: %s", self.page.url)
            if self.storage_state_path and (not self.use_persistent_context):
                os.makedirs(os.path.dirname(self.storage_state_path), exist_ok=True)
                await self.page.context.storage_state(path=self.storage_state_path)
            if self.debug:
                logging.info("Logged in successfully")
        else:
            if self.debug:
                logging.info("Already authenticated; current URL: %s", self.page.url)
        # Emit explicit checkpoint before continuing
        logging.info("Login check completed; current URL: %s", self.page.url)

    def _attach_navigation_logging(self) -> None:
        if not self.page:
            return
        page = self.page
        def _on_nav(frame):
            try:
                if frame == page.main_frame:
                    logging.info("Navigated to %s", frame.url)
            except Exception:
                pass
        page.on("framenavigated", _on_nav)

    async def search_people(self, keywords: List[str], locations: List[str], max_results: int = 25) -> List[SearchResult]:
        assert self.page is not None
        if self.debug:
            logging.info("Searching people with keywords: %s", ", ".join(keywords))

        search_results: List[SearchResult] = []
        page_number = 1
        stagnant_rounds = 0
        max_stagnant_rounds = 3  # Number of rounds without new profiles before trying next page
        processed_urls = set()  # Track processed URLs to avoid duplicates
        
        while len(search_results) < max_results:
            # Build URL with page number
            url = self._build_search_url(keywords, page_number)
            if self.debug:
                logging.info("Loading search page %d", page_number)
            
            await self.page.goto(url, wait_until="domcontentloaded")
            await self._human_pause()
            
            page_round = 0
            results_before_round = len(search_results)
            
            # Scroll through current page to load more results
            while len(search_results) < max_results and page_round < 10:  # Max 10 scroll rounds per page
                page_round += 1
                
                # Find all search result containers
                result_containers = await self.page.locator("div.ohQFMJgsahXYKwkqjYqSorBCVcblSnDIgFig").all()
                
                if len(result_containers) == 0:
                    # Fallback to finding profile links directly
                    cards = await self.page.locator("a[href*='/in/']").all()
                    if len(cards) == 0:
                        cards = await self.page.locator("a.app-aware-link:has(img)").all()
                    
                    for card in cards:
                        href = await card.get_attribute("href")
                        if not href or "/in/" not in href:
                            continue
                        profile_url = href.split("?")[0]
                        if profile_url not in processed_urls:
                            processed_urls.add(profile_url)
                            # For fallback, we don't have connection status
                            search_results.append(SearchResult(
                                name="",  # Will be filled during profile scraping
                                headline=None,
                                location=None,
                                profile_url=profile_url,
                                connection_status="unknown"
                            ))
                            if len(search_results) >= max_results:
                                break
                else:
                    # Process each search result container
                    for result_container in result_containers:
                        # Find the profile link within this container
                        profile_link = result_container.locator("a[href*='/in/']").first
                        if await profile_link.count() == 0:
                            continue
                        
                        href = await profile_link.get_attribute("href")
                        if not href or "/in/" not in href:
                            continue
                        
                        profile_url = href.split("?")[0]
                        
                        # Check if already processed
                        if profile_url in processed_urls:
                            continue
                        
                        processed_urls.add(profile_url)
                        
                        # Extract name from the profile link or nearby text
                        name = ""
                        name_elem = result_container.locator("span[aria-hidden='true']").first
                        if await name_elem.count() > 0:
                            name_text = await name_elem.text_content()
                            if name_text:
                                name = name_text.strip()
                        
                        # Find the button in the same container to check connection status
                        button = result_container.locator("button").first
                        connection_status = "unknown"
                        
                        if await button.count() > 0:
                            # First try to get button text content
                            button_text = await button.text_content()
                            
                            # If no text, try to get the aria-label which often has the action
                            if not button_text or button_text.strip() == "":
                                button_aria_label = await button.get_attribute("aria-label")
                                if button_aria_label:
                                    button_text = button_aria_label
                            
                            if button_text:
                                button_text = button_text.strip().lower()
                                
                                # If button says "message", we're already connected - skip this profile
                                if "message" in button_text:
                                    if self.debug:
                                        logging.debug("Skipping connected profile: %s (button: Message)", profile_url)
                                    continue
                                
                                # If button says "connect" or "follow", we're not connected - add to list
                                elif "connect" in button_text or "follow" in button_text or "invite" in button_text:
                                    connection_status = "not_connected"
                                    if self.debug:
                                        logging.debug("Adding unconnected profile: %s (button: %s)", profile_url, button_text.title())
                                else:
                                    # Unknown button state, check if it could be a connect button
                                    # Sometimes buttons have generic text, so let's be less strict
                                    if self.debug:
                                        logging.debug("Profile with unclear button: %s (button: %s), adding anyway", profile_url, button_text)
                                    connection_status = "not_connected"  # Assume not connected if unclear
                            else:
                                # No button text even after checking aria-label
                                # This might be a UI issue, let's add them anyway
                                if self.debug:
                                    logging.debug("Profile with no button text: %s, adding anyway", profile_url)
                                connection_status = "not_connected"
                        else:
                            # No button found - this could mean various things
                            # Let's add them anyway to be safe
                            if self.debug:
                                logging.debug("Profile with no button found: %s, adding anyway", profile_url)
                            connection_status = "unknown"
                        
                        # Only skip if we're certain they're connected (message button)
                        # Otherwise, add to results
                        
                        # Add to results
                        search_results.append(SearchResult(
                            name=name,
                            headline=None,
                            location=None,
                            profile_url=profile_url,
                            connection_status=connection_status
                        ))
                        
                        if len(search_results) >= max_results:
                            break
                
                # Scroll to load more on current page
                await self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                if self.debug:
                    logging.debug("Page %d, round %d: collected %d profiles so far", page_number, page_round, len(search_results))
                await self._human_pause()
            
            # Check if we found new profiles on this page
            results_after_round = len(search_results)
            if results_after_round == results_before_round:
                stagnant_rounds += 1
                if self.debug:
                    logging.info("No new profiles found on page %d (stagnant round %d/%d)", page_number, stagnant_rounds, max_stagnant_rounds)
            else:
                stagnant_rounds = 0  # Reset stagnant counter if we found profiles
                if self.debug:
                    logging.info("Found %d new profiles on page %d", results_after_round - results_before_round, page_number)
            
            # If we've been stagnant for too many rounds, try next page
            if stagnant_rounds >= max_stagnant_rounds:
                if self.debug:
                    logging.info("No new profiles after %d rounds, trying next page", stagnant_rounds)
                page_number += 1
                stagnant_rounds = 0  # Reset for new page
                continue
            
            # If we haven't found any profiles on this page after scrolling, try next page
            if results_after_round == results_before_round:
                page_number += 1
                if self.debug:
                    logging.info("No profiles found on page %d, moving to page %d", page_number - 1, page_number)
                continue
        
        if self.debug:
            logging.info("Collected %d search results across %d pages", len(search_results[:max_results]), page_number)
        return search_results[:max_results]

    def _build_search_url(self, keywords: List[str], page_number: int) -> str:
        # Use a single keywords string, spaces become %20
        joined = "%20".join([k.strip().replace(" ", "%20") for k in keywords if k.strip()])
        base = f"https://www.linkedin.com/search/results/people/?keywords={joined}&page={page_number}"
        return base

    async def search_people_listings(self, keywords: List[str], locations: List[str], max_results: int = 25) -> List[SearchResult]:
        assert self.page is not None
        results: List[SearchResult] = []
        page_number = 1
        stagnant_rounds = 0
        while len(results) < max_results:
            url = self._build_search_url(keywords, page_number)
            if self.debug:
                logging.info("Loading search page %d", page_number)
            await self.page.goto(url, wait_until="domcontentloaded")
            await self._human_pause()
            item_loc = self.page.locator("li.reusable-search__result-container")
            count = await item_loc.count()
            if count == 0:
                # Try a simpler anchor selection as fallback
                cards = await self.page.locator("a[href*='/in/']").all()
                if len(cards) == 0:
                    # Fallback to the old selector
                    cards = await self.page.locator("a.app-aware-link[href*='/in/']").all()
                if len(cards) == 0:
                    if self.debug:
                        logging.info("No results on page %d; stopping.", page_number)
                    break
                # Convert anchors to results
                for card in cards:
                    href = await card.get_attribute("href")
                    if not href:
                        continue
                    profile_url = href.split("?")[0]
                    name_text = await card.text_content()
                    sr = SearchResult(name=(name_text or '').strip(), headline=None, location=None, profile_url=profile_url)
                    results.append(sr)
                    if len(results) >= max_results:
                        break
            else:
                start_len = len(results)
                for i in range(count):
                    item = item_loc.nth(i)
                    link = item.locator("a[href*='/in/']").first
                    if await link.count() == 0:
                        link = item.locator("a.app-aware-link[href*='/in/']").first
                    href = await link.get_attribute("href") if await link.count() > 0 else None
                    if not href:
                        continue
                    profile_url = href.split("?")[0]
                    # Try extracting name
                    name_el = item.locator("span[aria-hidden=true]").first
                    name_text = (await name_el.text_content()) if await name_el.count() > 0 else None
                    # Headline and location candidates
                    headline_el = item.locator("div.entity-result__primary-subtitle").first
                    if await headline_el.count() == 0:
                        headline_el = item.locator("div.entity-result__secondary-subtitle").first
                    headline_text = (await headline_el.text_content()) if await headline_el.count() > 0 else None
                    location_el = item.locator("div.entity-result__secondary-subtitle").nth(1)
                    location_text = (await location_el.text_content()) if await location_el.count() > 0 else None
                    sr = SearchResult(
                        name=(name_text or '').strip(),
                        headline=(headline_text or '').strip() if headline_text else None,
                        location=(location_text or '').strip() if location_text else None,
                        profile_url=profile_url,
                    )
                    results.append(sr)
                    if len(results) >= max_results:
                        break
                new_count = len(results) - start_len
                if new_count == 0:
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0
                logging.info("Search page %d: +%d new, total %d", page_number, new_count, len(results))
            if len(results) >= max_results:
                break
            if stagnant_rounds >= 2:
                if self.debug:
                    logging.info("No new results after %d pages; stopping.", stagnant_rounds)
                break
            page_number += 1
        return results[:max_results]

    async def scrape_profile(self, profile_url: str) -> Profile:
        assert self.page is not None
        if self.debug:
            logging.info("Scraping profile: %s", profile_url)
        await self.page.goto(profile_url)
        await self.page.wait_for_load_state("domcontentloaded")

        def safe_text(selector: str) -> Optional[str]:
            return selector.inner_text().strip() if selector else None

        name = await self.page.locator("h1:text-matches('.*', 's')").first.text_content()
        name = name.strip() if name else ""
        headline = await self.page.locator("div.text-body-medium.break-words").first.text_content()
        headline = headline.strip() if headline else ""
        location = await self.page.locator("span.text-body-small.inline.t-black--light.break-words").first.text_content()
        location = location.strip() if location else None

        # About
        about = None
        about_section = self.page.locator("section:has(h2:has-text('About'))")
        if await about_section.count() > 0:
            about_text = await about_section.locator("div.inline-show-more-text").first.text_content()
            if about_text:
                about = about_text.strip()

        # Experience bullets (simple extraction)
        experiences: List[str] = []
        exp_section = self.page.locator("section:has(h2:has-text('Experience'))")
        if await exp_section.count() > 0:
            items = exp_section.locator("li").all()
            for item in await items:
                title = await item.locator("span[aria-hidden=true]").nth(0).text_content()
                company = await item.locator("span[aria-hidden=true]").nth(1).text_content()
                line = " - ".join([t.strip() for t in [title, company] if t])
                if line:
                    experiences.append(line)

        # Skills (limited visibility without auth depth)
        skills: List[str] = []
        skill_section = self.page.locator("section:has(h2:has-text('Skills'))")
        if await skill_section.count() > 0:
            chips = await skill_section.locator("span[aria-hidden=true]").all()
            for chip in chips[:15]:
                text = await chip.text_content()
                if text:
                    skills.append(text.strip())

        followers_count: Optional[int] = None
        follower_el = self.page.locator("span:has-text('followers')").first
        if await follower_el.count() > 0:
            text = await follower_el.text_content()
            if text:
                # e.g., "1,234 followers"
                num = ''.join(ch for ch in text if ch.isdigit())
                if num:
                    try:
                        followers_count = int(num)
                    except ValueError:
                        followers_count = None

        return Profile(
            name=name,
            headline=headline,
            location=location,
            profile_url=profile_url,
            about=about,
            experiences=experiences,
            skills=skills,
            followers_count=followers_count,
        )

    async def connect_with_note(self, profile_url: str, note: str) -> bool:
        assert self.page is not None
        if self.debug:
            logging.info("Connecting with note: %s", profile_url)
        await self.page.goto(profile_url)
        await self.page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)  # Wait for page to fully load

        # Try to find Connect button - check multiple locations and scenarios
        connect_button = None
        
        # Method 1: Try direct Connect button with aria-label containing "Invite" and "to connect"
        try:
            connect_button = await self.page.wait_for_selector(
                'button[aria-label*="Invite"][aria-label*="to connect"]',
                timeout=3000
            )
            if self.debug:
                logging.info("Found direct connect button using aria-label selector")
        except:
            pass
        
        # Method 2: Try button with span containing "Connect" text
        if not connect_button:
            try:
                connect_button = await self.page.wait_for_selector(
                    'button:has(span.artdeco-button__text:text("Connect"))',
                    timeout=3000
                )
                if self.debug:
                    logging.info("Found direct connect button using span text selector")
            except:
                pass
        
        # Method 3: Try role-based selector for direct connect button
        if not connect_button:
            connect_candidates = await self.page.get_by_role("button", name=re.compile(r"Connect", re.IGNORECASE)).all()
            for candidate in connect_candidates:
                if await candidate.is_visible():
                    connect_button = candidate
                    if self.debug:
                        logging.info("Found direct connect button using role selector")
                    break
        
        # Method 4: Check if Connect button is hidden in "More" dropdown menu
        if not connect_button:
            if self.debug:
                logging.info("Direct connect button not found, checking More dropdown")
            
            # Look for profile overflow action button (More button)
            more_button_selectors = [
                'button[id*="profile-overflow-action"]',  # Your specific case
                'button[aria-label*="More actions"]',
                'button:has-text("More")',
                'button[data-control-name="overflow_menu"]'
            ]
            
            more_button = None
            for selector in more_button_selectors:
                try:
                    more_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if more_button and await more_button.is_visible():
                        if self.debug:
                            logging.info("Found More button using selector: %s", selector)
                        break
                except:
                    continue
            
            if more_button:
                # Click the More button to open dropdown
                await more_button.click()
                await asyncio.sleep(1.5)  # Wait for dropdown to appear
                
                # Now look for Connect button in the dropdown
                dropdown_connect_selectors = [
                    'button[aria-label*="Invite"][aria-label*="to connect"]',  # Your specific case
                    'div[role="menu"] button:has-text("Connect")',
                    'ul[role="menu"] button:has-text("Connect")',
                    'div.artdeco-dropdown__content button:has-text("Connect")',
                    'button:has(span:text("Connect"))'
                ]
                
                for selector in dropdown_connect_selectors:
                    try:
                        connect_button = await self.page.wait_for_selector(selector, timeout=2000)
                        if connect_button and await connect_button.is_visible():
                            if self.debug:
                                logging.info("Found connect button in dropdown using selector: %s", selector)
                            break
                    except:
                        continue
                
                # Also try looking for specific element IDs like ember77 mentioned in your case
                if not connect_button:
                    try:
                        # Look for any button with ID starting with "ember" that might be a connect button
                        ember_buttons = await self.page.locator('button[id^="ember"]').all()
                        for ember_btn in ember_buttons:
                            aria_label = await ember_btn.get_attribute("aria-label")
                            if aria_label and "connect" in aria_label.lower():
                                connect_button = ember_btn
                                if self.debug:
                                    logging.info("Found connect button using ember ID with aria-label: %s", aria_label)
                                break
                    except:
                        pass
            else:
                if self.debug:
                    logging.warning("More button not found")
        
        if not connect_button:
            logging.warning("Connect button not found on profile: %s", profile_url)
            return False

        # Click Connect button
        try:
            await connect_button.click()
            if self.debug:
                logging.info("Clicked connect button successfully")
        except Exception as e:
            logging.error("Failed to click connect button: %s", str(e))
            return False
        
        await asyncio.sleep(2)  # Wait for modal to appear
        
        # Handle the connection modal - look for "Add a note" button
        add_note_btn = None
        
        # Enhanced selectors for "Add a note" button
        add_note_selectors = [
            'button[aria-label="Add a note"]',
            'button[aria-label*="Add a note"]',
            'button:has-text("Add a note")',
            'button:has(span:text("Add a note"))',
            'button.artdeco-button--secondary:has-text("Add a note")'
        ]
        
        for selector in add_note_selectors:
            try:
                add_note_btn = await self.page.wait_for_selector(selector, timeout=3000)
                if add_note_btn and await add_note_btn.is_visible():
                    if self.debug:
                        logging.info("Found 'Add a note' button using selector: %s", selector)
                    break
            except:
                continue
        
        # If still not found, try role-based selector
        if not add_note_btn:
            try:
                add_note_candidates = await self.page.get_by_role("button", name=re.compile(r"Add.*note", re.IGNORECASE)).all()
                for candidate in add_note_candidates:
                    if await candidate.is_visible():
                        add_note_btn = candidate
                        if self.debug:
                            logging.info("Found 'Add a note' button using role selector")
                        break
            except:
                pass
        
        if not add_note_btn:
            logging.warning("'Add a note' button not found in modal")
            # Try to send without note if we can't find the add note button
            try:
                send_without_note_selectors = [
                    'button:has-text("Send without a note")',
                    'button[aria-label*="Send without a note"]',
                    'button.artdeco-button--primary:has-text("Send")'
                ]
                
                send_without_note = None
                for selector in send_without_note_selectors:
                    try:
                        send_without_note = await self.page.wait_for_selector(selector, timeout=2000)
                        if send_without_note and await send_without_note.is_visible():
                            break
                    except:
                        continue
                
                if send_without_note:
                    logging.info("Sending without note as fallback")
                    await send_without_note.click()
                    return True
                else:
                    return False
            except Exception as e:
                logging.error("Failed to send without note: %s", str(e))
                return False
        
        # Click "Add a note" button
        try:
            await add_note_btn.click()
            if self.debug:
                logging.info("Clicked 'Add a note' button, waiting for textarea")
        except Exception as e:
            logging.error("Failed to click 'Add a note' button: %s", str(e))
            return False
        
        await asyncio.sleep(1.5)  # Wait for textarea to appear
        
        # Fill in the note - enhanced textarea detection
        try:
            textarea = None
            textarea_selectors = [
                'textarea[name="message"]',
                'textarea#custom-message', 
                'textarea[placeholder*="note"]',
                'textarea[placeholder*="message"]',
                'div[role="dialog"] textarea',
                'textarea'  # Fallback to any textarea
            ]
            
            for selector in textarea_selectors:
                try:
                    textarea = await self.page.wait_for_selector(selector, timeout=2000)
                    if textarea and await textarea.is_visible():
                        if self.debug:
                            logging.info("Found textarea using selector: %s", selector)
                        break
                except:
                    continue
            
            if textarea:
                await textarea.fill(note[:300])  # LinkedIn allows up to 300 chars
                if self.debug:
                    logging.info("Filled connection note: %s", note[:50] + "...")
            else:
                logging.warning("Could not find message textarea")
                return False
        except Exception as e:
            logging.warning("Could not fill message textarea: %s", str(e))
            return False
        
        await asyncio.sleep(1)
        
        # Use test_mode from instance configuration
        if self.test_mode:
            logging.info("TEST MODE: Not sending connection request. Would have sent with note: %s", note[:100] + "...")
            # Close the modal instead of sending
            try:
                cancel_btn = self.page.get_by_role("button", name="Cancel").first
                if await cancel_btn.count() > 0:
                    await cancel_btn.click()
                    logging.info("Closed connection modal (test mode)")
                else:
                    await self.page.keyboard.press("Escape")
            except:
                await self.page.keyboard.press("Escape")
        else:
            # Actually send the connection request
            try:
                # Enhanced Send button detection
                send_btn = None
                send_selectors = [
                    'button:has-text("Send")',
                    'button[aria-label*="Send"]',
                    'button.artdeco-button--primary:has-text("Send")',
                    'div[role="dialog"] button:has-text("Send")'
                ]
                
                for selector in send_selectors:
                    try:
                        send_btn = await self.page.wait_for_selector(selector, timeout=2000)
                        if send_btn and await send_btn.is_visible():
                            break
                    except:
                        continue
                
                if send_btn:
                    await send_btn.click()
                    logging.info("Connection request sent with note")
                    return True
                else:
                    # Try role-based selector as final fallback
                    send_btn = self.page.get_by_role("button", name="Send").first
                    if await send_btn.count() > 0:
                        await send_btn.click()
                        logging.info("Connection request sent with note")
                        return True
                    else:
                        logging.error("Could not find Send button")
                        return False
            except Exception as e:
                logging.error("Failed to send connection request: %s", str(e))
                return False
        
        return True  # Return True for testing purposes

    async def _human_pause(self):
        if self.max_action_delay_ms <= 0 and self.min_action_delay_ms <= 0:
            await asyncio.sleep(0.8)
            return
        low = max(0, self.min_action_delay_ms) / 1000.0
        high = max(low, self.max_action_delay_ms / 1000.0)
        await asyncio.sleep(random.uniform(low, high))


