"""Test 10 persona queries — clears cache per query before running."""
import uuid
from agents.graph import process_query
from core.cache import get_redis_client, _make_cache_key

QUERIES = [
    "hi",
    "who are you",
    "tell me about yourself",
    "what makes you different from other engineers",
    "tell me about TaxSetu",
    "what do you think about AI replacing engineers",
    "why should I hire you",
    "what are you working on",
    "what is your engineering philosophy",
    "how can I contact you",
]

if __name__ == "__main__":
    redis = get_redis_client()
    for q in QUERIES:
        try:
            redis.delete(_make_cache_key(q))
        except Exception:
            pass
        result = process_query(q, str(uuid.uuid4()))
        print("=" * 70)
        print(f"QUERY: {q}")
        print(f"intent: {result.get('intent')} | source: {result.get('response_source')} | rag_score: {result.get('rag_score')}")
        print(f"RESPONSE:\n{result.get('final_response', '')}")
        if result.get("error"):
            print(f"ERROR: {result.get('error')}")
