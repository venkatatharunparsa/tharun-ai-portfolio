"""
Response style profiles — adapt tone/depth by visitor type.
"""
from core.visitor_intent import detect_visitor_type

STYLE_PROFILES = {
    "recruiter": {
        "label": "recruiter",
        "instruction": (
            "STYLE: Recruiter mode.\n"
            "- Keep it concise: 2-4 sentences.\n"
            "- Lead with impact, ownership, and business value.\n"
            "- Mention concrete outcomes (hackathons, shipped systems, reliability).\n"
            "- End with a clear hiring CTA (resume/contact/next step)."
        ),
        "max_sentences": 4,
    },
    "engineer": {
        "label": "technical evaluator",
        "instruction": (
            "STYLE: Technical evaluator mode.\n"
            "- Go deeper: architecture, agent design, trade-offs, and failure handling.\n"
            "- Include stack specifics and why those choices were made.\n"
            "- Explain orchestration flow (planner/router/tools/guardrails) when relevant.\n"
            "- Prefer precise engineering language over marketing language."
        ),
        "max_sentences": 8,
    },
    "student": {
        "label": "student learner",
        "instruction": (
            "STYLE: Mentor mode for learners.\n"
            "- Be encouraging and practical.\n"
            "- Explain concepts simply, then give a concrete next step.\n"
            "- Share how you learned by building, not just reading.\n"
            "- Suggest one actionable learning path tied to your projects."
        ),
        "max_sentences": 6,
    },
    "collaborator": {
        "label": "builder/collaborator",
        "instruction": (
            "STYLE: Collaborator mode.\n"
            "- Focus on problem framing, product thinking, and execution speed.\n"
            "- Highlight where you can co-build and what you bring to a team.\n"
            "- Keep tone founder-friendly and action-oriented.\n"
            "- Offer a clear collaboration next step."
        ),
        "max_sentences": 5,
    },
    "curious": {
        "label": "curious visitor",
        "instruction": (
            "STYLE: Story-driven mode.\n"
            "- Use an engaging origin story hook, then the technical core.\n"
            "- Keep language accessible but credible.\n"
            "- End with one interesting follow-up angle."
        ),
        "max_sentences": 5,
    },
    "unknown": {
        "label": "general visitor",
        "instruction": (
            "STYLE: Balanced mode.\n"
            "- Clear, confident, first-person.\n"
            "- Mix story + substance.\n"
            "- Keep it readable and avoid unnecessary jargon."
        ),
        "max_sentences": 5,
    },
}


def resolve_visitor_type(conversation_history: list | None, current_query: str = "") -> str:
    """Resolve visitor type for style selection."""
    return detect_visitor_type(conversation_history or [], current_query)


def get_style_instruction(visitor_type: str) -> str:
    """Return style block to inject into synthesis prompts."""
    profile = STYLE_PROFILES.get(visitor_type, STYLE_PROFILES["unknown"])
    return profile["instruction"]


def get_style_meta(conversation_history: list | None, current_query: str = "") -> dict:
    """Return style metadata for logging/UI."""
    visitor_type = resolve_visitor_type(conversation_history, current_query)
    profile = STYLE_PROFILES.get(visitor_type, STYLE_PROFILES["unknown"])
    return {
        "visitor_type": visitor_type,
        "style_label": profile["label"],
        "max_sentences": profile["max_sentences"],
    }
