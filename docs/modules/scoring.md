## Popularity score

File: `automation/scoring.py`

Heuristics (0–100):
- Followers: scaled contribution up to +30
- Seniority keywords in headline/about: +10 each
- Skills count: +1 each up to +20
- Experience count: +1.5 each up to +20
- Capped at 100

Tune the weights in `compute_popularity_score` as you learn what correlates with your outreach goals.


