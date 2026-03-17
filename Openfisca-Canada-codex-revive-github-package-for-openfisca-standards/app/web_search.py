"""Lightweight web search for Canadian legislation context.

Uses DuckDuckGo to find relevant legislation snippets from official
Canadian government websites.  Results are injected into the Ollama
system prompt so the LLM can cite up-to-date legal references.

Every chat interaction triggers a search so the model always has access
to the most current available legislation.
"""

from __future__ import annotations

import time

from duckduckgo_search import DDGS

# ---------------------------------------------------------------------------
# Search execution (DuckDuckGo, scoped to Canadian gov sites)
# ---------------------------------------------------------------------------

_SITE_QUALIFIERS = "site:laws-lois.justice.gc.ca OR site:canada.ca"
_BASE_QUERY = (
    "MVOHWR Canada Labour Code motor vehicle operator"
    " hours of work overtime regulations"
)

_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
_CACHE_TTL = 300  # seconds


def search_legislation(
    user_message: str,
    max_results: int = 3,
) -> list[dict[str, str]]:
    """Search DuckDuckGo for Canadian legislation relevant to *user_message*.

    The user's message is combined with a standing base query so that even
    vague follow-ups (e.g. "how many hours is that?") still return relevant
    legislation results.

    Returns a list of dicts with keys ``title``, ``url``, ``snippet``.
    Never raises – returns an empty list on failure.
    """
    query = f"{user_message} {_BASE_QUERY} {_SITE_QUALIFIERS}"
    cache_key = query.strip().lower()[:200]
    now = time.time()

    if cache_key in _cache:
        ts, cached = _cache[cache_key]
        if now - ts < _CACHE_TTL:
            return cached

    try:
        with DDGS() as ddgs:
            raw = list(
                ddgs.text(
                    query,
                    max_results=max_results,
                    region="ca-en",
                )
            )
    except Exception:  # noqa: BLE001 – must never break the chatbot
        return []

    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw
    ]

    _cache[cache_key] = (now, results)
    return results


# ---------------------------------------------------------------------------
# Format results for LLM context injection
# ---------------------------------------------------------------------------


def format_search_context(results: list[dict[str, str]]) -> str:
    """Format search results into a text block for the system prompt."""
    if not results:
        return ""

    lines = [
        "",
        "Relevant Canadian legislation search results (use these to support your answer):",
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"  [{i}] {r['title']}")
        lines.append(f"      URL: {r['url']}")
        lines.append(f"      {r['snippet']}")
    lines.append("")
    lines.append("Cite the URL(s) when referencing legislation in your answer.")
    return "\n".join(lines)
