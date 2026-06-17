"""
LLM text generation with Gemini primary and Groq fallback.
Each provider tries primary API key, then fallback key, before moving on.
Skips Gemini entirely during quota cooldown to avoid 10-50s wasted retries.
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import google.generativeai as genai
from groq import Groq

from config import GENERATION_MODEL, FAST_MODEL, LLM_TIMEOUT_SEC
from core.provider_keys import get_gemini_keys, get_groq_keys, try_with_keys

logger = logging.getLogger(__name__)
_llm_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm")

# Track Gemini quota state globally
_gemini_quota_exhausted_until: float = 0.0


def is_gemini_available() -> bool:
    """Check if Gemini quota cooldown has passed."""
    return time.time() > _gemini_quota_exhausted_until


def mark_gemini_exhausted(cooldown_seconds: int = 300) -> None:
    """Mark Gemini as exhausted for cooldown period."""
    global _gemini_quota_exhausted_until
    _gemini_quota_exhausted_until = time.time() + cooldown_seconds
    logger.info("Gemini quota cooldown active for %ss — using Groq", cooldown_seconds)


def _call_gemini(prompt: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GENERATION_MODEL)
    response = model.generate_content(prompt)
    return response.text.strip()


def _call_groq(prompt: str, max_tokens: int, api_key: str) -> str:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


def _run_llm(fn, label: str) -> str | None:
    future = _llm_executor.submit(fn)
    try:
        text = future.result(timeout=LLM_TIMEOUT_SEC)
        return text if text else None
    except FuturesTimeoutError:
        logger.warning("%s LLM call timed out after %ss", label, LLM_TIMEOUT_SEC)
        return None
    except Exception as exc:
        logger.warning("%s LLM call failed: %s", label, exc)
        return None


def _is_quota_error(exc: Exception) -> bool:
    err = str(exc).lower()
    return "quota" in err or "429" in err


def _try_gemini_keys(prompt: str) -> str | None:
    """Try Gemini keys; mark cooldown immediately on quota errors."""
    if not is_gemini_available():
        return None

    gemini_keys = get_gemini_keys()
    if not gemini_keys:
        return None

    for index, key in enumerate(gemini_keys):
        slot = "primary" if index == 0 else f"fallback-{index}"
        try:
            return _call_gemini(prompt, key)
        except Exception as exc:
            if _is_quota_error(exc):
                mark_gemini_exhausted(300)
                logger.warning("gemini %s quota exhausted: %s", slot, exc)
                return None
            logger.warning("gemini %s key failed: %s", slot, exc)

    return None


def generate_with_fallback(prompt: str, max_tokens: int = 300) -> str:
    """
    Try Gemini first (if not in cooldown), fall back to Groq.
    Skips Gemini entirely if recently quota-exhausted — saves 10-50s.
    """
    if is_gemini_available():
        text = _run_llm(lambda: _try_gemini_keys(prompt), "gemini")
        if text:
            return text
        if not is_gemini_available():
            logger.info("Skipping Gemini — quota cooldown active, using Groq")
        else:
            mark_gemini_exhausted(300)
            logger.info("Gemini unavailable — using Groq fallback")

    groq_keys = get_groq_keys()
    if groq_keys:
        text = _run_llm(
            lambda: try_with_keys(
                groq_keys,
                "groq",
                lambda key: _call_groq(prompt, max_tokens, key),
            ),
            "groq",
        )
        if text:
            return text

    raise RuntimeError("All LLM providers failed")


def generate_text(prompt: str, max_tokens: int = 300) -> str:
    """Backward-compatible alias for generate_with_fallback."""
    return generate_with_fallback(prompt, max_tokens=max_tokens)
