import asyncio
import time

from automation.linkedin import LinkedInAutomation


async def _pause_duration(min_ms: int, max_ms: int) -> float:
    li = LinkedInAutomation(
        email="e",
        password="p",
        headless=True,
        slow_mo_ms=0,
        navigation_timeout_ms=10_000,
        storage_state_path=None,
        use_persistent_context=False,
        user_data_dir=None,
        browser_channel=None,
        debug=False,
        min_action_delay_ms=min_ms,
        max_action_delay_ms=max_ms,
    )
    # call the internal pause without launching browser
    start = time.perf_counter()
    await li._human_pause()
    end = time.perf_counter()
    return end - start


def test_human_pause_bounds_event_loop():
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        d = loop.run_until_complete(_pause_duration(100, 200))
        assert 0.095 <= d <= 0.25
    finally:
        loop.close()


