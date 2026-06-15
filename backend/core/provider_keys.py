"""
Multi-key fallback for Gemini and Groq API calls.
Tries primary key first, then GEMINI_API_KEY_FALLBACK / GROQ_API_KEY_FALLBACK.
"""
import logging
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _unique_keys(*keys: str | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for key in keys:
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def get_gemini_keys() -> list[str]:
    from config import GEMINI_API_KEY, GEMINI_API_KEY_FALLBACK

    return _unique_keys(GEMINI_API_KEY, GEMINI_API_KEY_FALLBACK)


def get_groq_keys() -> list[str]:
    from config import GROQ_API_KEY, GROQ_API_KEY_FALLBACK

    return _unique_keys(GROQ_API_KEY, GROQ_API_KEY_FALLBACK)


def try_with_keys(
    keys: list[str],
    label: str,
    call: Callable[[str], T],
) -> T | None:
    """Try call(api_key) for each key until one succeeds."""
    if not keys:
        return None

    for index, key in enumerate(keys):
        slot = "primary" if index == 0 else f"fallback-{index}"
        try:
            return call(key)
        except Exception as exc:
            logger.warning("%s %s key failed: %s", label, slot, exc)

    return None
