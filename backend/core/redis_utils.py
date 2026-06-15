"""
Redis utility — wraps all Redis calls with timeout.
Upstash REST can be slow from India — fail open, never block user.
"""
import threading

from upstash_redis import Redis

from config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN

REDIS_TIMEOUT_SEC = 2.5


def get_redis_client() -> Redis:
    return Redis(
        url=UPSTASH_REDIS_REST_URL,
        token=UPSTASH_REDIS_REST_TOKEN,
    )


def safe_redis_get(key: str) -> str | None:
    """Get from Redis with timeout — returns None on timeout or error."""
    try:
        result = [None]
        error = [None]

        def do_get():
            try:
                client = get_redis_client()
                result[0] = client.get(key)
            except Exception as e:
                error[0] = e

        t = threading.Thread(target=do_get, daemon=True)
        t.start()
        t.join(timeout=REDIS_TIMEOUT_SEC)

        if t.is_alive():
            return None
        if error[0]:
            return None
        return result[0]

    except Exception:
        return None


def safe_redis_set(key: str, value: str, ttl: int) -> None:
    """Set in Redis with timeout — fails silently, never blocks user."""

    def do_set():
        try:
            client = get_redis_client()
            client.setex(key, ttl, value)
        except Exception:
            pass

    t = threading.Thread(target=do_set, daemon=True)
    t.start()
    t.join(timeout=REDIS_TIMEOUT_SEC)
