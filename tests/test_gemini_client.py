import types
import asyncio

from automation.gemini_client import GeminiClient
from automation.linkedin import Profile


class DummyModel:
    def __init__(self):
        pass


def test_gemini_calls_model_new_sdk():
    # Fake google.genai path
    dummy = DummyModel()
    class FakeGenAI:
        class Client:
            def __init__(self, api_key):
                class Models:
                    def generate_content(self, model, contents):
                        return types.SimpleNamespace(text="ok")
                self.models = Models()
    client = GeminiClient(api_key="x", model_name="gemini-1.5-flash", genai_module=FakeGenAI)

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
        # Response shape validated via ok text above
    finally:
        loop.close()


