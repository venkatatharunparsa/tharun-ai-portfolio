"""

Redis Cache Layer — Upstash Redis via REST API.

Caches common query→response pairs to save LLM quota.

TTL: 24 hours for RAG responses.

"""

import hashlib
import json
import logging

from upstash_redis import Redis

from config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN

from core.redis_utils import safe_redis_get, safe_redis_set

logger = logging.getLogger(__name__)



CACHE_TTL_SECONDS = 86400  # 24 hours

CACHE_PREFIX = "tharun_ai:"





def get_redis_client() -> Redis:

    """Get Upstash Redis client."""

    return Redis(

        url=UPSTASH_REDIS_REST_URL,

        token=UPSTASH_REDIS_REST_TOKEN

    )





def _make_cache_key(query: str) -> str:

    """

    Generate a consistent cache key from a query.

    Normalizes the query (lowercase, stripped) before hashing.

    """

    normalized = query.lower().strip()

    query_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]

    return f"{CACHE_PREFIX}{query_hash}"





def get_cached_response(query: str) -> str | None:

    """

    Check Redis cache for a query.

    Returns cached response string or None if not found or Redis is slow.

    """

    cached = safe_redis_get(_make_cache_key(query))

    if cached:

        data = json.loads(cached)

        return data.get("response")

    return None





def flush_all_cache() -> None:

    """

    Flush entire Redis cache.

    Call this after any persona or knowledge base update.

    """

    try:

        redis = get_redis_client()

        keys_result = redis.keys(f"{CACHE_PREFIX}*")

        if keys_result:

            for key in keys_result:

                redis.delete(key)

            logger.info("Flushed %s cached responses.", len(keys_result))
        else:
            logger.info("Cache already empty.")
    except Exception as e:
        logger.warning("Cache flush error: %s", e)





def cache_response(query: str, response: str) -> None:

    """Store a query→response pair in Redis with TTL (non-blocking)."""

    key = _make_cache_key(query)

    data = json.dumps({"response": response, "query": query})

    safe_redis_set(key, data, CACHE_TTL_SECONDS)


