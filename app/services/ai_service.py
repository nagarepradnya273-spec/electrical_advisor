"""
Optional AI layer for the Electrical Advisor.

Design principle (spec section 30): AI must not invent technical
specifications or safety advice. So this module does NOT ask Claude to
generate guidance - it only asks Claude to pick which *existing,
admin-authored* AdvisorProblem record best matches a free-text query.
The actual explanation / safe checks / danger level always come from the
database, never from the model's own words.

If ANTHROPIC_API_KEY isn't set, or the API call fails for any reason
(network, rate limit, timeout), this returns None and the caller falls
back to plain keyword matching - the Advisor always keeps working.
"""
import httpx

from app.config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def ai_available() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def ai_match_problem_slug(query: str, problems: list[dict], place_context: str = "any") -> str | None:
    """
    problems: list of {"slug": ..., "title": ..., "keywords": ...}
    Returns the slug Claude picked, or None if it found no good match
    (or the call failed) - in which case the caller should fall back to
    keyword matching.
    """
    if not settings.ANTHROPIC_API_KEY or not problems:
        return None

    problem_list = "\n".join(
        f"- slug: {p['slug']} | title: {p['title']} | keywords: {p['keywords']}"
        for p in problems
    )

    system_prompt = (
        "You match a user's plain-language description of a household/shop "
        "electrical problem to the closest entry in a fixed list of known "
        "problems. Only ever choose a slug from the list given to you - "
        "never invent a new one, and never give advice yourself. "
        "If nothing in the list reasonably matches, respond with exactly: none. "
        "Respond with ONLY the slug or 'none', with no other text."
    )
    user_prompt = (
        f"Known problems (place context: {place_context}):\n{problem_list}\n\n"
        f'User\'s description: "{query}"\n\n'
        "Best matching slug:"
    )

    try:
        response = httpx.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 20,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=8.0,
        )
        response.raise_for_status()
        data = response.json()
        text = "".join(block.get("text", "") for block in data.get("content", [])).strip().lower()
    except Exception:
        return None

    if not text or text == "none":
        return None

    valid_slugs = {p["slug"] for p in problems}
    return text if text in valid_slugs else None
