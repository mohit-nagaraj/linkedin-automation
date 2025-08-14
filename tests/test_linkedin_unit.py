import pytest
from automation.linkedin import Profile


def test_profile_dataclass_fields():
    p = Profile(
        name="X",
        headline="Y",
        location="Z",
        profile_url="https://u",
        about=None,
        experiences=[],
        skills=["a"],
        followers_count=None,
    )
    assert p.name == "X"
    assert p.skills == ["a"]


