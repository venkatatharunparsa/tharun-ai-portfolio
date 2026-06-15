"""Pre-deploy smoke test — 5 critical /chat paths."""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
SID = "smoke-predeploy-001"


def post_chat(query: str) -> dict:
    payload = json.dumps({"query": query, "session_id": SID}).encode()
    req = urllib.request.Request(
        f"{BASE}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    data["_elapsed_ms"] = round((time.time() - t0) * 1000)
    return data


def main():
    # Test 1 — Health
    with urllib.request.urlopen(f"{BASE}/health", timeout=10) as resp:
        health = json.loads(resp.read().decode())
    print("TEST 1 health:", health)

    tests = [
        ("TEST 2 hi", "hi", lambda r: r.get("response_source") == "instant" and r["_elapsed_ms"] < 2000),
        ("TEST 3 TaxSetu", "tell me about TaxSetu", lambda r: r.get("response_source") in ("agent", "rag", "tool") and len(r.get("response", "")) > 20),
        ("TEST 4 compare", "compare TaxSetu and InfraGenie", lambda r: r.get("response_source") in ("agent", "tool") and "compare_projects" in (r.get("tools_used") or [])),
        ("TEST 5 salary", "what is your salary", lambda r: r.get("response_source") == "fallback"),
    ]

    for label, query, check in tests:
        try:
            r = post_chat(query)
            ok = check(r)
            print(f"{label}: {'PASS' if ok else 'FAIL'}")
            print(f"  source={r.get('response_source')} ms={r['_elapsed_ms']} tools={r.get('tools_used')}")
            print(f"  preview={r.get('response','')[:100]}")
        except Exception as exc:
            print(f"{label}: FAIL — {exc}")


if __name__ == "__main__":
    main()
