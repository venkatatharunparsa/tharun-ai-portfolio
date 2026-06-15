"""Per-visitor session memory in Redis + in-process cache."""
import json
import threading

from config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN
from core.redis_utils import safe_redis_get, safe_redis_set

SESSION_PREFIX = "tharun_session:"
SESSION_TTL_SECONDS = 7200
MAX_SESSION_MESSAGES = 8

_local_sessions: dict[str, list[dict]] = {}
_local_lock = threading.Lock()


def _session_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}{session_id}"


def _redis_write_async(key: str, payload: str) -> None:
    """Fire-and-forget Redis write — never block the response path."""
    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        return
    threading.Thread(
        target=safe_redis_set,
        args=(key, payload, SESSION_TTL_SECONDS),
        daemon=True,
    ).start()


def _load_session_history(session_id: str) -> list[dict]:
    with _local_lock:
        if session_id in _local_sessions:
            return list(_local_sessions[session_id][-MAX_SESSION_MESSAGES:])

    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        return []
    raw = safe_redis_get(_session_key(session_id))
    if not raw:
        return []
    data = json.loads(raw)
    messages = data.get("messages", [])[-MAX_SESSION_MESSAGES:]
    with _local_lock:
        _local_sessions[session_id] = list(messages)
    return messages


def get_session_history(session_id: str) -> list[dict]:
    if not session_id:
        return []
    if session_id.startswith("test-"):
        with _local_lock:
            return list(_local_sessions.get(session_id, []))
    return _load_session_history(session_id)


def _save_session_history(session_id: str, messages: list[dict]) -> None:
    trimmed = messages[-MAX_SESSION_MESSAGES:]
    with _local_lock:
        _local_sessions[session_id] = list(trimmed)
    _redis_write_async(_session_key(session_id), json.dumps({"messages": trimmed}))


def save_session_history(session_id: str, messages: list[dict]) -> None:
    if not session_id or not messages:
        return
    _save_session_history(session_id, messages[-MAX_SESSION_MESSAGES:])


def append_session_turn(session_id: str, user_text: str, assistant_text: str) -> None:
    if not session_id:
        return
    with _local_lock:
        history = list(_local_sessions.get(session_id, []))
    if not history:
        history = _load_session_history(session_id)
    history.append({"role": "user", "text": user_text})
    history.append({"role": "assistant", "text": assistant_text})
    _save_session_history(session_id, history[-MAX_SESSION_MESSAGES:])


def merge_histories(server: list[dict], client: list[dict]) -> list[dict]:
    """Prefer the longer valid history."""
    if not server:
        return client[-MAX_SESSION_MESSAGES:]
    if not client:
        return server[-MAX_SESSION_MESSAGES:]
    if len(client) > len(server):
        return client[-MAX_SESSION_MESSAGES:]
    return server[-MAX_SESSION_MESSAGES:]
