"""
LangGraph Agent Orchestration Graph — Tharun AI Portfolio.

This is the main pipeline that processes every user query.
Each node is an agent. State flows through the graph based on conditions.

Pipeline:
  instant_greeting → verify → classify_intent → route_agent → validate_response → finalize
"""
import random
import time
from typing import Literal
from langgraph.graph import StateGraph, END
from agents import AgentState
from agents.verification_agent import verification_agent
from agents.intent_classifier import intent_classifier_agent
from agents.smalltalk_agent import smalltalk_agent
from agents.tool_agent import tool_agent
from agents.contact_agent import contact_agent
from core.generation import generate_text
from tools.github_tool import search_github_data
from core.session_memory import (
    get_session_history,
    append_session_turn,
    merge_histories,
)
from core.persona import normalize_query, enforce_persona, enforce_education_facts, enforce_contact_email
from core.fast_path import get_fast_path_response, warmup_fast_path_cache

INSTANT_GREETINGS = {
    "hi", "hey", "hello", "hii", "heyy", "helloo",
    "hi there", "hey there", "good morning", "good evening",
    "good afternoon", "namaste", "sup", "what's up", "yo",
}

INSTANT_GREETING_RESPONSES = [
    "Hey! I'm Tharun — agentic AI engineer and builder. Ask me about my projects, skills, or what I'm working on.",
    "Hi there! Tharun here. I work on AI that acts, not just chats. What do you want to know?",
    "Hey, good to have you here! I'm Tharun — I build agentic AI systems. What brings you by?",
    "Hello! I'm Tharun. Ask me anything — my projects, my stack, my philosophy, or how to reach me.",
]


def _is_instant_greeting(query: str) -> bool:
    normalized = normalize_query(query)
    return normalized in INSTANT_GREETINGS


def _is_instant_bypass(query: str) -> bool:
    """Only pure greetings bypass the agent — everything else uses tools + LLM."""
    return normalize_query(query) in INSTANT_GREETINGS


def instant_greeting_node(state: AgentState) -> AgentState:
    """Instant path for pure greetings and pre-cached fast-path queries."""
    query = normalize_query(state["user_query"])
    if query in INSTANT_GREETINGS:
        return {
            **state,
            "verification_status": "pass",
            "intent": "small_talk",
            "final_response": random.choice(INSTANT_GREETING_RESPONSES),
            "response_source": "instant",
            "cache_hit": False,
            "rag_grounded": False,
            "agent_steps": [{"type": "instant", "detail": "Greeting — no tools needed"}],
            "tools_used": [],
        }

    fast_response = get_fast_path_response(query)
    if fast_response:
        return {
            **state,
            "verification_status": "pass",
            "intent": "availability",
            "final_response": fast_response,
            "response_source": "cache",
            "cache_hit": True,
            "rag_grounded": True,
            "agent_steps": [{"type": "cache", "detail": "Pre-cached why_hire response"}],
            "tools_used": [],
        }

    return state


def route_after_greeting(state: AgentState) -> Literal["validate", "verify"]:
    """Instant greetings and fast-path cache hits skip verification."""
    if state.get("response_source") in ("instant", "cache"):
        return "validate"
    return "verify"


def check_cache_node(state: AgentState) -> AgentState:
    """
    Plan B: cache disabled for main agent path — every turn runs tools visibly.
    (Instant greetings bypass this node anyway.)
    """
    return {**state, "cache_hit": False}


def route_by_verification(state: AgentState) -> Literal["check_cache", "validate_response"]:
    """Route after verification — pass goes to cache check, fail still validates response."""
    if state["verification_status"] == "pass":
        return "check_cache"
    return "validate_response"


def route_by_cache(state: AgentState) -> Literal["classify_intent", "validate_response"]:
    """If cache hit — validate then finish. Otherwise classify intent."""
    if state.get("cache_hit"):
        return "validate_response"
    return "classify_intent"


def route_by_intent(state: AgentState) -> Literal["agent", "smalltalk", "contact", "github"]:
    """Route to agentic tool loop, contact, github, or smalltalk."""
    intent = state.get("intent")
    if intent == "small_talk":
        return "smalltalk"
    if intent == "contact":
        return "contact"
    if intent == "github":
        return "github"
    return "agent"


def github_agent_node(state: AgentState) -> AgentState:
    """Handle GitHub-specific queries with live API data."""
    try:
        github_data = search_github_data(state["user_query"])
        prompt = f"""You are Tharun. Answer this question about your GitHub using this live data:

{github_data}

Question: {state['user_query']}

Answer naturally in first person, 2-3 sentences. Use specific numbers from the data."""

        response = generate_text(prompt, max_tokens=300)

        return {
            **state,
            "final_response": response,
            "response_source": "github_live",
            "rag_grounded": False,
            "agent_steps": [{"type": "github", "detail": "Fetched live GitHub API data"}],
            "tools_used": ["search_github_data"],
        }
    except Exception as e:
        return {
            **state,
            "final_response": (
                "You can check my GitHub directly at "
                "github.com/venkatatharunparsa — "
                "all my open source work is there."
            ),
            "response_source": "fallback",
            "error": str(e),
        }


def response_validator_node(state: AgentState) -> AgentState:
    """
    Gate 5 — Validate and trim response before sending to user.
    Enforces length limit and checks for empty responses.
    """
    from config import MAX_RESPONSE_CHARS
    response = (state.get("final_response") or "").strip().strip('"').strip("'")

    if not response or len(response) < 5:
        return {
            **state,
            "final_response": "I don't have verified info on that right now. Reach me directly at parsavenkatatharun@gmail.com",
            "response_source": "fallback",
        }

    response = enforce_persona(response, state.get("user_query", ""))
    response = enforce_education_facts(response, state.get("user_query", ""))
    response = enforce_contact_email(response)

    if len(response) > MAX_RESPONSE_CHARS:
        trimmed = response[:MAX_RESPONSE_CHARS]
        last_period = max(
            trimmed.rfind(". "),
            trimmed.rfind(".\n"),
            trimmed.rfind("! "),
            trimmed.rfind("? "),
        )
        if last_period > MAX_RESPONSE_CHARS // 2:
            response = trimmed[: last_period + 1]
        else:
            response = trimmed.rstrip() + "..."

    return {**state, "final_response": response}


def cache_response_node(state: AgentState) -> AgentState:
    """Plan B: do not cache agent responses — tools must run each time."""
    return state


def build_agent_graph():
    """
    Build and compile the LangGraph agent orchestration graph.
    Returns a compiled graph ready to invoke.
    """
    graph = StateGraph(AgentState)

    graph.add_node("instant_greeting", instant_greeting_node)
    graph.add_node("verify", verification_agent)
    graph.add_node("check_cache", check_cache_node)
    graph.add_node("classify_intent", intent_classifier_agent)
    graph.add_node("agent", tool_agent)
    graph.add_node("contact", contact_agent)
    graph.add_node("github", github_agent_node)
    graph.add_node("smalltalk", smalltalk_agent)
    graph.add_node("validate_response", response_validator_node)
    graph.add_node("cache_result", cache_response_node)

    graph.set_entry_point("instant_greeting")

    graph.add_conditional_edges("instant_greeting", route_after_greeting, {
        "validate": "validate_response",
        "verify": "verify",
    })

    graph.add_conditional_edges("verify", route_by_verification, {
        "check_cache": "check_cache",
        "validate_response": "validate_response",
    })

    graph.add_conditional_edges("check_cache", route_by_cache, {
        "classify_intent": "classify_intent",
        "validate_response": "validate_response",
    })

    graph.add_conditional_edges("classify_intent", route_by_intent, {
        "agent": "agent",
        "contact": "contact",
        "github": "github",
        "smalltalk": "smalltalk",
    })

    graph.add_edge("agent", "validate_response")
    graph.add_edge("contact", "validate_response")
    graph.add_edge("github", "validate_response")
    graph.add_edge("smalltalk", "validate_response")

    graph.add_edge("validate_response", "cache_result")
    graph.add_edge("cache_result", END)

    return graph.compile()


_graph = None


def get_graph():
    """Get or create the compiled agent graph."""
    global _graph
    if _graph is None:
        _graph = build_agent_graph()
    return _graph


def reset_graph() -> None:
    """Clear compiled graph (tests / hot reload)."""
    global _graph
    _graph = None


def process_query(
    user_query: str,
    session_id: str,
    language: str = "en",
    conversation_history: list | None = None,
) -> AgentState:
    """
    Main entry point for processing a user query through the full pipeline.

    Args:
        user_query: Text input from user (after STT)
        session_id: Unique session identifier
        language: Detected language code

    Returns:
        Final AgentState with response populated
    """
    start = time.time()

    fast_response = get_fast_path_response(user_query)
    if fast_response:
        from config import MAX_RESPONSE_CHARS

        response = enforce_education_facts(
            enforce_persona(fast_response.strip(), user_query),
            user_query,
        )
        if len(response) > MAX_RESPONSE_CHARS:
            trimmed = response[:MAX_RESPONSE_CHARS]
            last_period = max(
                trimmed.rfind(". "),
                trimmed.rfind(".\n"),
                trimmed.rfind("! "),
                trimmed.rfind("? "),
            )
            if last_period > MAX_RESPONSE_CHARS // 2:
                response = trimmed[: last_period + 1]
            else:
                response = trimmed.rstrip() + "..."

        append_session_turn(session_id, user_query, response)
        elapsed = (time.time() - start) * 1000
        return {
            "user_query": user_query,
            "session_id": session_id,
            "language": language,
            "verification_status": "pass",
            "verification_reason": None,
            "intent": "availability",
            "intent_confidence": None,
            "retrieved_chunks": None,
            "rag_score": None,
            "rag_grounded": True,
            "final_response": response,
            "response_source": "cache",
            "tts_provider": None,
            "audio_output": None,
            "cache_hit": True,
            "conversation_history": conversation_history or [],
            "error": None,
            "processing_time_ms": elapsed,
            "agent_steps": [{"type": "cache", "detail": "Pre-cached why_hire response"}],
            "tools_used": [],
            "action": None,
        }

    if _is_instant_bypass(user_query):
        merged_history = conversation_history or []
    else:
        server_history = get_session_history(session_id)
        merged_history = merge_histories(server_history, conversation_history or [])

    initial_state: AgentState = {
        "user_query": user_query,
        "session_id": session_id,
        "language": language,
        "verification_status": "pending",
        "verification_reason": None,
        "intent": None,
        "intent_confidence": None,
        "retrieved_chunks": None,
        "rag_score": None,
        "rag_grounded": None,
        "final_response": None,
        "response_source": None,
        "tts_provider": None,
        "audio_output": None,
        "cache_hit": False,
        "conversation_history": merged_history,
        "error": None,
        "processing_time_ms": None,
        "agent_steps": None,
        "tools_used": None,
        "action": None,
    }

    graph = get_graph()
    result = graph.invoke(initial_state)

    if result.get("verification_status") == "pass" and result.get("final_response"):
        if result.get("response_source") != "instant":
            append_session_turn(session_id, user_query, result["final_response"])

    result["processing_time_ms"] = (time.time() - start) * 1000
    return result
