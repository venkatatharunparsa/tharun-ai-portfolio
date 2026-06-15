"""
LLM text generation with Gemini primary and Groq fallback.
Each provider tries primary API key, then fallback key, before moving on.
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
_gemini_skip_until: float = 0.0


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
        temperature=0.3,
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


def generate_text(prompt: str, max_tokens: int = 300) -> str:
    """Generate text using Gemini (all keys), then Groq (all keys)."""
    global _gemini_skip_until
    gemini_keys = get_gemini_keys()
    if gemini_keys and time.time() >= _gemini_skip_until:
        text = _run_llm(
            lambda: try_with_keys(
                gemini_keys,
                "gemini",
                lambda key: _call_gemini(prompt, key),
            ),
            "gemini",
        )
        if text:
            return text
        _gemini_skip_until = time.time() + 300
        logger.info("Skipping Gemini for 5 min after quota/failure — using Groq")

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
