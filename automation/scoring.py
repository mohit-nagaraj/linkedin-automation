from __future__ import annotations

from typing import List, Optional
from .linkedin import Profile


def compute_popularity_score(profile: Profile, seniority_keywords: List[str]) -> float:
    score = 0.0

    # Followers influence
    if profile.followers_count:
        # Log-scaled weight
        score += min(30.0, (profile.followers_count / 1000.0) * 5.0)

    text_blob = " ".join(filter(None, [profile.headline, profile.about or ""]))
    text_blob_lower = text_blob.lower()

    # Seniority/role signals
    for kw in seniority_keywords:
        if kw.lower() in text_blob_lower:
            score += 10.0

    # Skills density
    skills_bonus = min(20.0, len(profile.skills) * 1.0)
    score += skills_bonus

    # Experience count bonus
    exp_bonus = min(20.0, len(profile.experiences) * 1.5)
    score += exp_bonus

    # Cap
    return round(min(score, 100.0), 2)


