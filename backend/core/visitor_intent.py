"""
Visitor Intent Detector — Tharun AI Portfolio.
After 2-3 turns, detects what kind of visitor this is.
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

CURIOUS_SIGNALS = [
    "interesting", "cool", "awesome", "impressive",
    "what is", "explain", "how does", "tell me about",
]


def detect_visitor_type(conversation_history: list) -> str:
    """Returns: recruiter | collaborator | student | curious | unknown"""
    if len(conversation_history) < 2:
        return "unknown"

    all_text = " ".join(
        msg.get("text", "").lower()
        for msg in conversation_history
        if msg.get("role") == "user"
    )

    scores = {
        "recruiter": sum(1 for s in RECRUITER_SIGNALS if s in all_text),
        "collaborator": sum(1 for s in COLLABORATOR_SIGNALS if s in all_text),
        "student": sum(1 for s in STUDENT_SIGNALS if s in all_text),
        "curious": sum(1 for s in CURIOUS_SIGNALS if s in all_text),
    }

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


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
    }
    return messages.get(visitor_type)
