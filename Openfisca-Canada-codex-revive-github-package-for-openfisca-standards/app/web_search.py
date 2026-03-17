"""Lightweight web search for Canadian legislation context.

Uses DuckDuckGo to find relevant legislation snippets from official
Canadian government websites.  Results are injected into the Ollama
system prompt so the LLM can cite up-to-date legal references.
"""

from __future__ import annotations

import re
import time

from duckduckgo_search import DDGS

# ---------------------------------------------------------------------------
# 1. Search trigger – detect legislation-related questions
# ---------------------------------------------------------------------------

_LEGISLATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(law|legislation|regulation|act|code|statute|section|part\s+III)\b",
        r"\b(canada\s+labour\s+code|clc|mvohwr|motor\s+vehicle\s+operator)\b",
        r"\b(current|latest|amended|updated|new|recent)\b.*\b(rule|regulation|law|standard)\b",
        r"\bwhat\s+does\s+the\s+(law|regulation|code)\s+say\b",
        r"\b(legal|rights|entitle|complaint|file\s+a\s+complaint)\b",
        r"\b(minimum\s+wage|overtime\s+rate|holiday\s+pay)\b",
        r"\b(SOR|C\.R\.C\.|DORS)\b",
    ]
]


def should_search(user_message: str) -> bool:
    """Return *True* when the message likely asks about legislation."""
    text = user_message.strip()
    if len(text) < 15:
        return False
    return any(pat.search(text) for pat in _LEGISLATION_PATTERNS)


# ---------------------------------------------------------------------------
# 2. Search execution (DuckDuckGo, scoped to Canadian gov sites)
# ---------------------------------------------------------------------------

_SITE_QUALIFIERS = "site:laws-lois.justice.gc.ca OR site:canada.ca"
_BASE_QUERY = "MVOHWR Canada Labour Code motor vehicle operator"

_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
_CACHE_TTL = 300  # seconds


def search_legislation(
    user_message: str,
    max_results: int = 3,
) -> list[dict[str, str]]:
    """Search DuckDuckGo for Canadian legislation relevant to *user_message*.

    Returns a list of dicts with keys ``title``, ``url``, ``snippet``.
    Never raises – returns an empty list on failure.
    """
    cache_key = user_message.strip().lower()[:200]
    now = time.time()

    if cache_key in _cache:
        ts, cached = _cache[cache_key]
        if now - ts < _CACHE_TTL:
            return cached

    try:
        with DDGS() as ddgs:
            raw = list(
                ddgs.text(
                    f"{user_message} {_BASE_QUERY} {_SITE_QUALIFIERS}",
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
# 3. Format results for LLM context injection
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
