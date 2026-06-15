"""
Verification Agent — Gate 1 of the Tharun AI pipeline.

This agent runs FIRST on every query before any LLM call.
It uses zero LLM quota — pure rule-based checks only.

Checks:
1. Is the query coherent? (not gibberish or mic noise)
2. Is it relevant to Tharun? (not completely off-topic)
3. Is it safe? (no blocked topics, no jailbreak attempts)
4. Is it an appropriate length? (not empty, not a wall of text)

Returns AgentState with verification_status = "pass" or "fail"
"""
import time
from agents import AgentState
from config import BLOCKED_TOPICS


# Phrases that indicate jailbreak or prompt injection attempts
JAILBREAK_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "you are now",
    "pretend you are",
    "act as if",
    "forget everything",
    "new persona",
    "disregard your",
    "override your",
    "system prompt",
    "you have no restrictions",
    "bypass",
    "jailbreak",
    "dan mode",
]

# Minimum and maximum query length
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 500

# Phrases that indicate completely off-topic conversation
OFF_TOPIC_PATTERNS = [
    "i'm not a product",
    "i am not a product",
    "i think you are",
    "you are a chef",
    "you are a doctor",
    "you are a lawyer",
    "corporate business",
    "i'm ready to go",
    "next one",
    "never mind",
    "tax save to god",
    "save to god",
]

OFF_TOPIC_RESPONSE = (
    "I'm Tharun — I can tell you about my projects, skills, experience, "
    "and how to reach me. What would you like to know?"
)

# Words that suggest the query is about Tharun or his work
RELEVANT_KEYWORDS = [
    # Greetings — always allow
    "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
    "howdy", "greetings", "sup", "what's up", "namaste",
    # Identity references
    "tharun", "you", "your", "he", "his", "him", "who",
    # Professional topics
    "project", "skill", "experience", "work", "build", "built",
    "ai", "agent", "portfolio", "resume", "cv",
    "contact", "hire", "job", "internship", "collaborate", "startup",
    "study", "education", "university", "college", "degree",
    # Project names
    "infragenie", "taxsetu", "nina", "visionsync", "astradeploy", "career guide",
    # Tech keywords
    "python", "fastapi", "cloud", "aws", "devops", "rag", "llm",
    "langchain", "langgraph", "gemini", "groq",
    # Question words — always allow
    "what", "how", "who", "when", "where", "why",
    "tell", "explain", "show", "describe", "about", "help",
    "can", "does", "did", "is", "are", "has", "have",
    # Action words
    "learn", "know", "find", "show", "give", "share",
]


def is_completely_off_topic(text: str) -> bool:
    """Detect queries that are clearly not about Tharun at all."""
    text_lower = text.lower()

    if any(pattern in text_lower for pattern in OFF_TOPIC_PATTERNS):
        return True

    words = text_lower.strip().split()
    if len(words) == 1 and len(words[0]) <= 2 and words[0] not in ["hi", "ok", "yo"]:
        return True

    return False


def is_gibberish(text: str) -> bool:
    """
    Check if text is mic noise or gibberish.
    A real query should have at least some alphabetic content.
    """
    alpha_chars = sum(1 for c in text if c.isalpha())
    return alpha_chars < 2


def contains_blocked_topic(text: str) -> tuple[bool, str]:
    """
    Check if query contains any blocked topic keywords.
    Returns (is_blocked, matched_topic).
    """
    text_lower = text.lower()
    for topic in BLOCKED_TOPICS:
        if topic.lower() in text_lower:
            return True, topic
    return False, ""


def contains_jailbreak(text: str) -> bool:
    """
    Check if query contains jailbreak or prompt injection patterns.
    """
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in JAILBREAK_PATTERNS)


def is_relevant_to_tharun(text: str) -> bool:
    """
    Check if the query is relevant to Tharun or his work.
    Very permissive — only blocks clearly off-topic queries.
    Greetings and general questions always pass.
    """
    text_lower = text.lower().strip()

    # Always allow very short inputs — likely greetings
    if len(text_lower.split()) <= 3:
        return True

    # Always allow question-style queries
    question_starters = [
        "what", "who", "how", "where", "when", "why",
        "tell", "can you", "do you", "is", "are", "does",
    ]
    if any(text_lower.startswith(q) for q in question_starters):
        return True

    return any(keyword in text_lower for keyword in RELEVANT_KEYWORDS)


def verification_agent(state: AgentState) -> AgentState:
    """
    Gate 1 — Verify query before any LLM call.

    Args:
        state: Current AgentState with user_query populated

    Returns:
        AgentState with verification_status set to 'pass' or 'fail'
        and verification_reason explaining why (if failed)
    """
    start = time.time()
    query = state["user_query"].strip()

    # Check 1: Empty or too short
    if len(query) < MIN_QUERY_LENGTH:
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": "Query too short — possibly empty mic input.",
            "final_response": "I didn't catch that. Could you please ask again?",
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000
        }

    # Check 2: Too long (potential prompt injection)
    if len(query) > MAX_QUERY_LENGTH:
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": "Query too long.",
            "final_response": "That's quite a long message! Could you keep it concise?",
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000
        }

    # Check 3: Gibberish check
    if is_gibberish(query):
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": "Query appears to be gibberish or mic noise.",
            "final_response": "I didn't catch that clearly. Could you try again?",
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000
        }

    # Check 4: Jailbreak detection
    if contains_jailbreak(query):
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": "Jailbreak attempt detected.",
            "final_response": "I'm here to talk about my work, projects, and experience. What would you like to know?",
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000
        }

    # Check 5: Off-topic non-sequitur
    if is_completely_off_topic(query):
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": "Off-topic query",
            "final_response": OFF_TOPIC_RESPONSE,
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000,
        }

    # Check 6: Blocked topic
    is_blocked, matched_topic = contains_blocked_topic(query)
    if is_blocked:
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": f"Blocked topic detected: {matched_topic}",
            "final_response": "That's outside what I can discuss. I'm here to talk about my work, projects, and experience.",
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000
        }

    # Check 7: Relevance check (soft — don't block, just flag)
    if not is_relevant_to_tharun(query):
        return {
            **state,
            "verification_status": "fail",
            "verification_reason": "Query not relevant to Tharun.",
            "final_response": "I'm Tharun — ask me about my projects, skills, experience, or how to reach me.",
            "response_source": "fallback",
            "processing_time_ms": (time.time() - start) * 1000
        }

    # All checks passed
    return {
        **state,
        "verification_status": "pass",
        "verification_reason": None,
        "processing_time_ms": (time.time() - start) * 1000
    }
