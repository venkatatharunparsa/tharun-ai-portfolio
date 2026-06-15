"""
Pre-cached fast-path responses for high-frequency recruiter queries.
Warmed on startup (memory + Redis) and served before the agent pipeline.
"""
import logging

from core.cache import cache_response
from core.persona import normalize_query

logger = logging.getLogger(__name__)

FAST_PATH_QUERIES = {
    "why should i hire you": "why_hire",
    "why hire you": "why_hire",
    "why should we hire you": "why_hire",
    "convince me to hire you": "why_hire",
}

WHY_HIRE_RESPONSE = (
    "Here's why I'd be worth hiring: I build agentic AI that acts — not just chats. "
    "TaxSetu automates GST compliance, NINA adds voice navigation, InfraGenie handles cloud ops, "
    "VisionSync does film pre-viz.\n\n"
    "End-to-end: LangGraph agents, RAG, FastAPI, voice. SIH internal winner at RGUKT; "
    "TaxSetu reached KSUM nationally.\n\n"
    "Still at RGUKT Basar (2027, CGPA 8.5) — projects speak louder than the timeline. "
    "I ship fast, build with guardrails, and design systems — not just prompts."
)

FAST_PATH_RESPONSES: dict[str, str] = {
    "why_hire": WHY_HIRE_RESPONSE,
}

# normalized query -> response text (populated on warmup)
_query_cache: dict[str, str] = {}


def warmup_fast_path_cache() -> None:
    """Pre-cache all fast-path query variants in memory and Redis."""
    global _query_cache
    _query_cache = {}

    for query, key in FAST_PATH_QUERIES.items():
        response = FAST_PATH_RESPONSES.get(key)
        if not response:
            continue
        normalized = normalize_query(query)
        _query_cache[normalized] = response
        cache_response(query, response)

    logger.info("Fast-path cache warmed: %s queries", len(_query_cache))


def get_fast_path_response(query: str) -> str | None:
    """Return pre-cached response for a fast-path query, or None."""
    return _query_cache.get(normalize_query(query))


def is_fast_path_query(query: str) -> bool:
    return normalize_query(query) in FAST_PATH_QUERIES
