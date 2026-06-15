from agents.rag_agent import rag_agent

state = {
    "user_query": "What is Tharun's engineering philosophy?",
    "session_id": "test",
    "language": "en",
    "verification_status": "pass",
    "verification_reason": None,
    "intent": "philosophy",
    "intent_confidence": 1.0,
    "retrieved_chunks": None,
    "rag_score": None,
    "rag_grounded": None,
    "final_response": None,
    "response_source": None,
    "tts_provider": None,
    "audio_output": None,
    "cache_hit": False,
    "error": None,
    "processing_time_ms": None,
}
out = rag_agent(state)
print("source:", out.get("response_source"))
print("score:", out.get("rag_score"))
print("error:", out.get("error"))
print("response:", (out.get("final_response") or "")[:300])
