"""
Persona enforcement — Tharun speaks as himself, never as an AI assistant.
"""
import re

from core.contact_actions import CONTACT_DATA

CANONICAL_EMAIL = CONTACT_DATA["email"]

# Wrong email variants the LLM sometimes hallucinates
WRONG_EMAIL_PATTERNS = [
    re.compile(r"tharun\.parsa@gmail\.com", re.I),
    re.compile(r"venkata\.tharun\.parsa@gmail\.com", re.I),
    re.compile(r"tharunparsa@gmail\.com", re.I),
    re.compile(r"venkatatharun@gmail\.com", re.I),
    re.compile(r"tharun@gmail\.com", re.I),
]

CANONICAL_IDENTITY_RESPONSE = (
    "I'm Venkata Tharun Parsa — Tharun. I'm an agentic AI engineer from India, "
    "studying Computer Science at RGUKT Basar (graduating 2027, CGPA 8.5). "
    "I build systems where AI actually acts — multi-agent pipelines, RAG, real workflows. "
    "Ask me about TaxSetu, NINA, InfraGenie, or what I'm working on."
)

INSTANT_IDENTITY_QUERIES = {
    "who is tharun",
    "who is venkata tharun parsa",
    "who is venkata tharun",
    "tell me about yourself",
    "tell me about tharun",
    "who are you",
    "what is tharun",
    "introduce yourself",
    "about yourself",
    "about tharun",
}

# Speaking as an AI product / assistant — not as Tharun the person
AI_SELF_PATTERNS = [
    re.compile(r"\bI'?m the AI\b", re.I),
    re.compile(r"\bI am the AI\b", re.I),
    re.compile(r"\bconversational AI\b", re.I),
    re.compile(r"\bdesigned to have a voice\b", re.I),
    re.compile(r"\bI'?m an AI (engineer|assistant|agent|system)\b", re.I),
    re.compile(r"\bTharun AI\b", re.I),
    re.compile(r"\bportfolio agent\b", re.I),
    re.compile(r"\bvirtual assistants?\b", re.I),
    re.compile(r"\bI'?m not just about chatbots\b", re.I),
    re.compile(r"\bI'?m about creating AI that\b", re.I),
    re.compile(r"\bspecialized in sharing information about\b", re.I),
    re.compile(r"\bhis portfolio\b", re.I),
    re.compile(r"\bask me about (him|he|his)\b", re.I),
]

IDENTITY_QUERY_HINTS = (
    "who is tharun",
    "who are you",
    "tell me about yourself",
    "about tharun",
    "introduce yourself",
    "who is venkata",
)


def normalize_query(query: str) -> str:
    return query.lower().strip().rstrip("!?. ,")


def is_identity_query(query: str) -> bool:
    return normalize_query(query) in INSTANT_IDENTITY_QUERIES


def has_persona_violation(text: str) -> bool:
    if not text:
        return True
    return any(p.search(text) for p in AI_SELF_PATTERNS)


def enforce_persona(text: str, user_query: str = "") -> str:
    """
    Return cleaned response. Falls back to canonical identity answer when
    the model mixes AI-assistant voice with first-person Tharun.
    """
    cleaned = text.strip()
    if not has_persona_violation(cleaned):
        return cleaned

    q = user_query.lower()
    if is_identity_query(user_query) or any(h in q for h in IDENTITY_QUERY_HINTS):
        return (
            "I'm Tharun — agentic AI engineer. Let me search my knowledge base for specifics."
        )

    # Generic fix: strip obvious AI-self phrases for other queries
    replacements = [
        (r"\bI'?m the AI that acts\b", "I build AI that acts"),
        (r"\bI'?m not the AI that chats\b", "I don't just build chatbots"),
        (r"\bI'?m an AI engineer\b", "I'm an agentic AI engineer"),
        (r"\bTharun AI\b", "I"),
        (r"\bchatbots or virtual assistants\b", "simple chatbots"),
    ]
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned, flags=re.I)

    if has_persona_violation(cleaned):
        return (
            "I'm Tharun — agentic AI engineer and builder. "
            "Ask me something specific about my projects, skills, or experience."
        )

    return cleaned


EDUCATION_QUERY_HINTS = (
    "graduat", "cgpa", "degree", "rgukt", "university", "college", "study", "studying",
)

CANONICAL_EDUCATION_RESPONSE = (
    "Not yet — I'm still studying Computer Science at RGUKT Basar. "
    "Expected graduation is 2027, and my CGPA is 8.5."
)

GRADUATION_HALLUCINATION = (
    re.compile(r"\b(completed|finished|earned|got) my (engineering )?degree\b", re.I),
    re.compile(r"\bI'?ve graduated\b", re.I),
    re.compile(r"\bI have graduated\b", re.I),
    re.compile(r"\balready graduated\b", re.I),
)


def is_education_query(query: str) -> bool:
    q = query.lower()
    return any(h in q for h in EDUCATION_QUERY_HINTS)


def enforce_education_facts(text: str, user_query: str) -> str:
    """Prevent graduation/CGPA hallucinations — KB says still studying until 2027."""
    if not is_education_query(user_query):
        return text

    q = user_query.lower()
    lower = text.lower()

    if any(p.search(text) for p in GRADUATION_HALLUCINATION):
        return CANONICAL_EDUCATION_RESPONSE

    if "graduat" in q and ("not" not in lower and "2027" not in text and "still" not in lower):
        if any(w in lower for w in ("yes", "completed", "finished", "done")):
            return CANONICAL_EDUCATION_RESPONSE

    if "2027" not in text and ("graduat" in q or "when do you" in q):
        return CANONICAL_EDUCATION_RESPONSE

    if "cgpa" in q and "8.5" not in text and "8" not in text:
        return f"{text.rstrip('.')}. My CGPA is 8.5 at RGUKT Basar — graduating 2027."

    return text


def enforce_contact_email(text: str) -> str:
    """Replace hallucinated or wrong email addresses with the canonical contact email."""
    if not text:
        return text

    placeholder = "__CANONICAL_EMAIL__"
    protected = text.replace(CANONICAL_EMAIL, placeholder)

    cleaned = protected
    for pattern in WRONG_EMAIL_PATTERNS:
        cleaned = pattern.sub(placeholder, cleaned)

    # Any other gmail address (hallucinated / corrupted) → canonical
    cleaned = re.sub(
        r"[\w.+-]+@gmail\.com",
        lambda m: placeholder if m.group(0) != placeholder else m.group(0),
        cleaned,
        flags=re.I,
    )

    return cleaned.replace(placeholder, CANONICAL_EMAIL)
