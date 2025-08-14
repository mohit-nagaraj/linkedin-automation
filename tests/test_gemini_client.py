import types
import asyncio

from automation.gemini_client import GeminiClient
from automation.linkedin import Profile


class DummyModel:
    def __init__(self):
        self.prompts = []

    def generate_content(self, prompt: str):
        self.prompts.append(prompt)
        return types.SimpleNamespace(text="ok")


def test_gemini_calls_model():
    # Build a fake generativeai module
    dummy = DummyModel()
    class FakeGenAI:
        def configure(self, api_key):
            pass
        def GenerativeModel(self, model_name):
            return dummy
    client = GeminiClient(api_key="x", model_name="gemini-1.5-flash", generativeai_module=FakeGenAI())

    profile = Profile(
        name="Jane",
        headline="CTO",
        location="Remote",
        profile_url="https://x",
        about="about",
        experiences=["a", "b"],
        skills=["go"],
        followers_count=100,
    )

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        s = loop.run_until_complete(client.summarize_profile(profile, "owner"))
        n = loop.run_until_complete(client.craft_connect_note(profile, "owner"))
        assert s == "ok"
        assert n == "ok"
        assert len(dummy.prompts) == 2
    finally:
        loop.close()


