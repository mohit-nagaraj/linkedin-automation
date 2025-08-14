from automation.scoring import compute_popularity_score
from automation.linkedin import Profile


def make_profile(**overrides):
    base = Profile(
        name="Jane Doe",
        headline="CTO at Acme Corp",
        location="Remote",
        profile_url="https://www.linkedin.com/in/janedoe",
        about="Builder of distributed systems. Speaker and OSS maintainer.",
        experiences=["CTO - Acme", "Staff Engineer - Beta"],
        skills=["Go", "Kubernetes", "AWS", "PostgreSQL"],
        followers_count=5000,
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def test_popularity_scales_with_followers():
    p1 = make_profile(followers_count=0)
    p2 = make_profile(followers_count=5000)
    s1 = compute_popularity_score(p1, ["cto", "founder"])
    s2 = compute_popularity_score(p2, ["cto", "founder"])
    assert s2 > s1


def test_keywords_increase_score():
    p = make_profile()
    base = compute_popularity_score(p, [])
    boosted = compute_popularity_score(p, ["cto"])
    assert boosted > base


def test_caps_at_or_below_100():
    p = make_profile(followers_count=1_000_000, experiences=["x"] * 100, skills=["y"] * 100)
    s = compute_popularity_score(p, ["cto", "founder", "vp engineering"])  # should cap
    assert s <= 100.0
    assert s >= 80.0


