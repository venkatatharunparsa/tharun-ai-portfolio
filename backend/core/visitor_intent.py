"""
Visitor Intent Detector — Tharun AI Portfolio.
Detects visitor type from conversation + latest query to enable proactive engagement.
"""

RECRUITER_SIGNALS = [
    "hire", "hiring", "job", "internship", "full-time",
    "opportunity", "position", "role", "team", "company",
    "resume", "cv", "experience", "background",
    "available", "availability", "notice period",
    "interview", "apply", "application",
]

COLLABORATOR_SIGNALS = [
    "collaborate", "collab", "work together", "build together",
    "startup", "co-founder", "project idea", "partnership",
    "open source", "contribute", "hackathon", "team up",
]

STUDENT_SIGNALS = [
    "student", "learn", "learning", "how did you",
    "tutorial", "guide", "suggest", "advice", "tips",
    "beginner", "start", "getting started", "course",
    "university", "college", "rgukt",
]

ENGINEER_SIGNALS = [
    "architecture", "agent orchestration", "langgraph", "rag pipeline",
    "vector", "pgvector", "fallback", "guardrail", "tool calling",
    "websocket", "latency", "scalability", "trade-off", "tradeoff",
    "system design", "multi-agent", "orchestrator", "retrieval",
    "embedding", "prompt", "inference", "deployment", "terraform",
]

CURIOUS_SIGNALS = [
    "interesting", "cool", "awesome", "impressive",
    "what is", "explain", "how does", "tell me about",
]


def detect_visitor_type(conversation_history: list, current_query: str = "") -> str:
    """Returns: recruiter | collaborator | student | curious | unknown."""
    user_turns = [
        msg.get("text", "").lower()
        for msg in conversation_history
        if msg.get("role") == "user"
    ]
    if current_query:
        user_turns.append(current_query.lower())
    if not user_turns:
        return "unknown"

    all_text = " ".join(user_turns)

    scores = {
        "recruiter": sum(1 for s in RECRUITER_SIGNALS if s in all_text),
        "collaborator": sum(1 for s in COLLABORATOR_SIGNALS if s in all_text),
        "student": sum(1 for s in STUDENT_SIGNALS if s in all_text),
        "engineer": sum(2 for s in ENGINEER_SIGNALS if s in all_text),
        "curious": sum(1 for s in CURIOUS_SIGNALS if s in all_text),
    }

    best = max(scores, key=scores.get)
    return best if scores[best] >= 1 else "unknown"


def should_send_proactive(conversation_history: list, visitor_type: str) -> bool:
    """
    Send proactive guidance every ~4 user turns for known visitor types,
    unless we already sent one very recently.
    """
    if visitor_type == "unknown":
        return False

    user_turn_count = sum(1 for m in conversation_history if m.get("role") == "user")
    if user_turn_count < 3 or user_turn_count % 4 != 0:
        return False

    recent_assistant = [
        (m.get("text") or "").lower()
        for m in conversation_history[-4:]
        if m.get("role") == "assistant"
    ]
    proactive_markers = ("by the way", "sounds like you might", "if you're learning agentic ai")
    return not any(any(marker in t for marker in proactive_markers) for t in recent_assistant)


def get_proactive_message(visitor_type: str) -> str | None:
    """Return a proactive message based on detected visitor type."""
    messages = {
        "recruiter": (
            "By the way — if you're evaluating me for a role, "
            "you can download my resume below or reach me directly "
            "at parsavenkatatharun@gmail.com. I respond fast."
        ),
        "collaborator": (
            "Sounds like you might be interested in building something. "
            "I'm open to startup collaborations and interesting "
            "technical projects — reach out at "
            "parsavenkatatharun@gmail.com."
        ),
        "student": (
            "If you're learning agentic AI, my GitHub has "
            "open-source projects you can study — "
            "github.com/venkatatharunparsa"
        ),
        "engineer": (
            "If you want a deeper technical walkthrough, ask me about "
            "agent orchestration, RAG grounding, or guardrail design — "
            "I can go architecture-level."
        ),
    }
    return messages.get(visitor_type)
