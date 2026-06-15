"""Live GitHub profile data for Tharun AI portfolio."""
import json
from collections import Counter

import httpx

GITHUB_USERNAME = "venkatatharunparsa"
GITHUB_API = "https://api.github.com"


def _get_json(url: str) -> dict | list:
    headers = {"Accept": "application/vnd.github+json"}
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def search_github_data(query: str) -> str:
    """
    Fetch live GitHub stats and return a text summary for LLM grounding.
    """
    user = _get_json(f"{GITHUB_API}/users/{GITHUB_USERNAME}")
    repos = _get_json(
        f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos"
        "?sort=updated&per_page=30&type=owner"
    )
    events = _get_json(
        f"{GITHUB_API}/users/{GITHUB_USERNAME}/events/public?per_page=10"
    )

    languages: Counter = Counter()
    total_stars = 0
    repo_summaries = []

    for repo in repos if isinstance(repos, list) else []:
        if repo.get("fork"):
            continue
        lang = repo.get("language") or "Unknown"
        languages[lang] += 1
        stars = repo.get("stargazers_count", 0)
        total_stars += stars
        repo_summaries.append(
            f"- {repo.get('name')}: {lang}, {stars} stars, "
            f"updated {repo.get('updated_at', '')[:10]}"
        )

    top_langs = languages.most_common(5)
    recent_events = []
    for ev in (events if isinstance(events, list) else [])[:5]:
        ev_type = ev.get("type", "")
        repo_name = ev.get("repo", {}).get("name", "")
        created = ev.get("created_at", "")[:10]
        recent_events.append(f"- {ev_type} on {repo_name} ({created})")

    summary = {
        "username": GITHUB_USERNAME,
        "profile_url": user.get("html_url"),
        "public_repos": user.get("public_repos"),
        "followers": user.get("followers"),
        "bio": user.get("bio"),
        "total_stars_across_repos": total_stars,
        "top_languages": [{"language": l, "repo_count": c} for l, c in top_langs],
        "recent_repos": repo_summaries[:10],
        "recent_activity": recent_events,
        "query": query,
    }
    return json.dumps(summary, indent=2)
