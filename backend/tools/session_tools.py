"""Session memory tools."""
from core.session_memory import get_session_history
from core.generation import generate_text


def summarize_conversation(session_id: str = "", history: list | None = None) -> dict:
    if history:
        messages = history
    else:
        messages = get_session_history(session_id) if session_id else []

    if not messages:
        return {
            "session_id": session_id,
            "turn_count": 0,
            "summary": "No prior conversation in this session.",
        }

    transcript = "\n".join(
        f"{'Visitor' if m['role'] == 'user' else 'Tharun'}: {m['text']}"
        for m in messages
    )
    try:
        summary = generate_text(
            f"Summarize this portfolio chat in 2-3 sentences as Tharun (first person):\n\n{transcript}",
            max_tokens=150,
        )
    except Exception:
        summary = transcript[-500:]

    return {
        "session_id": session_id,
        "turn_count": len(messages) // 2,
        "summary": summary,
        "raw_turns": len(messages),
    }
