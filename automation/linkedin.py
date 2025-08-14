from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import asyncio
import random
import time
import logging

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


class LinkedInAutomation:
    def __init__(self, email: str, password: str, headless: bool = False, slow_mo_ms: int = 0, navigation_timeout_ms: int = 30000, storage_state_path: str | None = None, use_persistent_context: bool = True, user_data_dir: str | None = None, browser_channel: str | None = None, debug: bool = False, min_action_delay_ms: int = 0, max_action_delay_ms: int = 0):
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
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self) -> "LinkedInAutomation":
        self.playwright = await async_playwright().start()
        launch_args = dict(channel=self.browser_channel) if self.browser_channel else {}
        if self.use_persistent_context and self.user_data_dir:
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
            context = await self.browser.new_context(storage_state=storage)
        self.page = await context.new_page()
        self.page.set_default_timeout(self.navigation_timeout_ms)
        if self.debug:
            logging.info("Browser context ready (persistent=%s, user_data_dir=%s)", self.use_persistent_context, self.user_data_dir)
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
            # Wait for either feed to load or a visible error/2FA prompt
            try:
                await self.page.wait_for_url("**/feed**", timeout=self.navigation_timeout_ms)
            except Exception:
                # As a fallback, wait for main nav to appear
                await self.page.wait_for_selector("nav.global-nav", timeout=self.navigation_timeout_ms)
            if self.storage_state_path and (not self.use_persistent_context):
                os.makedirs(os.path.dirname(self.storage_state_path), exist_ok=True)
                await self.page.context.storage_state(path=self.storage_state_path)
            if self.debug:
                logging.info("Logged in successfully")

    async def search_people(self, keywords: List[str], locations: List[str], max_results: int = 25) -> List[str]:
        assert self.page is not None
        query = "%20".join([k.replace(" ", "%20") for k in keywords])
        if self.debug:
            logging.info("Searching people: %s", ", ".join(keywords))
        await self.page.goto(f"https://www.linkedin.com/search/results/people/?keywords={query}")

        # Optionally filter by locations if available
        # For simplicity, rely on keyword search; location filtering can be added via UI interaction.

        profile_urls: List[str] = []
        while len(profile_urls) < max_results:
            cards = await self.page.locator("a.app-aware-link:has(img)" ).all()
            for card in cards:
                href = await card.get_attribute("href")
                if not href:
                    continue
                if "/in/" in href and href not in profile_urls:
                    profile_urls.append(href.split("?")[0])
                    if len(profile_urls) >= max_results:
                        break
            # Scroll to load more
            await self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await self._human_pause()
        return profile_urls[:max_results]

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

        # Try connect flow
        connect_button = self.page.get_by_role("button", name="Connect").first
        if await connect_button.count() == 0:
            # Fallback in actions dropdown
            more_btn = self.page.get_by_role("button", name="More").first
            if await more_btn.count() > 0:
                await more_btn.click()
                connect_button = self.page.get_by_role("button", name="Connect").first
        if await connect_button.count() == 0:
            return False

        await connect_button.click()
        add_note_btn = self.page.get_by_role("button", name="Add a note").first
        if await add_note_btn.count() == 0:
            return False
        await add_note_btn.click()
        await self.page.fill("textarea[name='message']", note[:280])
        send_btn = self.page.get_by_role("button", name="Send").first
        if await send_btn.count() == 0:
            return False
        await send_btn.click()
        if self.debug:
            logging.info("Connection request sent")
        return True

    async def _human_pause(self):
        if self.max_action_delay_ms <= 0 and self.min_action_delay_ms <= 0:
            await asyncio.sleep(0.8)
            return
        low = max(0, self.min_action_delay_ms) / 1000.0
        high = max(low, self.max_action_delay_ms / 1000.0)
        await asyncio.sleep(random.uniform(low, high))


