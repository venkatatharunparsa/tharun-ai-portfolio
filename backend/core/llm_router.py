"""
LLM router — selects Gemini Flash or Groq LLaMA based on task type.
Checks Redis cache before any LLM call.
"""
from typing import Literal

from core.cache import get_cached_response, cache_response

LLMProvider = Literal["gemini", "groq"]


def route_llm(task: str) -> LLMProvider:
    """
    Select the appropriate LLM provider for a given task.
    Intent classification and smalltalk → Groq; RAG generation → Gemini.
    """
    groq_tasks = {"intent", "smalltalk", "fast"}
    if task in groq_tasks:
        return "groq"
    return "gemini"


def cached_llm_call(cache_key: str, llm_fn, *args, **kwargs):
    """
    Execute an LLM call with Redis cache lookup first.
    Returns cached result if available, otherwise calls llm_fn and caches result.
    """
    cached = get_cached_response(cache_key)
    if cached is not None:
        return cached

    try:
        result = llm_fn(*args, **kwargs)
        if isinstance(result, str):
            cache_response(cache_key, result)
        return result
    except Exception:
        return None
