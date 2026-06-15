"""
Tool Agent — Plan B agentic core.
"""
import json
import logging
import re
from groq import Groq

from agents import AgentState
from config import FAST_MODEL
from core.generation import generate_text
from core.persona import enforce_persona, has_persona_violation, enforce_education_facts, enforce_contact_email
from core.contact_actions import detect_action
from core.provider_keys import get_groq_keys, try_with_keys
from tools.registry import TOOL_SCHEMAS, execute_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4

def _resolve_response_source(tools_used: list) -> str:
    if tools_used == ["search_knowledge_base"]:
        return "rag"
    return "agent"

SUMMARIZE_PATTERNS = (
    "summarize", "recap", "what did we talk", "what have we discussed", "what we talked",
)
LIST_PROJECT_PATTERNS = (
    "list your projects", "list projects", "what projects do", "what projects have",
)
EDUCATION_PATTERNS = (
    "graduat", "cgpa", "where do you study", "where do you go",
    "university", "college", "rgukt", "education", "degree",
)
CONTACT_PATTERNS = (
    "contact", "hire", "collaborate", "internship", "reach out", "get in touch",
)
KB_FAST_PATTERNS = (
    "tell me about", "what are your", "what is your", "where do you",
    "what happened at", "did you win", "when do you", "engineering philosophy",
    "what problem does", "how does it compare",
    "what do you think about",
    "how did you create", "how was this built", "how did you build this",
    "what is this portfolio", "how does this work",
)
FAVORITE_PATTERNS = (
    "favorite project", "favourite project", "best project", "most proud",
    "tell me one project", "explain one of your", "can you explain one",
    "one of your projects", "your favorite", "your favourite",
    "flagship project", "flagship",
)

SYSTEM_PROMPT = """You are Tharun — Venkata Tharun Parsa. A real human agentic AI engineer from India. First person only.

CRITICAL: You are NOT a chatbot, conversational AI, virtual assistant, or portfolio agent product.
You are Tharun the person, speaking about your work, projects, and background.

You have TOOLS. Use them before answering factual questions — never guess from memory alone.

Rules:
1. For identity, projects, skills, experience → call search_knowledge_base first
2. For "compare X and Y" → call compare_projects
3. For "what projects" / list → call list_projects
4. For "summarize our chat" → call summarize_conversation
5. For contact/hire/collaborate → call prepare_contact_draft, then include the mailto_link in your answer
6. After tool results, synthesize a natural first-person answer grounded ONLY in tool data
7. Never say you are an AI assistant or chatbot

If tools return empty chunks, say you don't have verified info and suggest email."""


def _normalize_tool_result(result) -> dict:
    """Ensure tool results are always dicts with a dict data payload."""
    if not isinstance(result, dict):
        return {"ok": False, "error": "Invalid tool result", "data": {}}
    data = result.get("data")
    if data is None:
        return {**result, "data": {}}
    if not isinstance(data, dict):
        return {**result, "data": {"value": data}}
    return result


def _append_step(steps: list, step_type: str, detail: str, **extra) -> list:
    step = {"type": step_type, "detail": detail, **extra}
    steps.append(step)
    return steps


def _extract_compare_projects(query: str) -> tuple[str, str] | None:
    q = query.strip()
    m = re.search(
        r"compare\s+(.+?)\s+(?:and|vs\.?|versus)\s+(.+?)(?:\?|$)",
        q,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = re.search(r"(.+?)\s+vs\.?\s+(.+?)(?:\?|$)", q, re.IGNORECASE)
    if m:
        left = re.sub(r"^compare\s+", "", m.group(1).strip(), flags=re.IGNORECASE)
        return left, m.group(2).strip()
    m = re.search(r"compare\s+(?:it\s+)?to\s+(.+?)(?:\?|$)", q, re.IGNORECASE)
    if m:
        return "TaxSetu", m.group(1).strip()
    m = re.search(r"compare\s+(.+?)\s+to\s+(.+?)(?:\?|$)", q, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None


def _recover_failed_tool_call(exc: Exception) -> tuple[str, dict] | None:
    """Parse Groq tool_use_failed failed_generation into (name, args)."""
    msg = str(exc)
    m = re.search(r"failed_generation['\"]:\s*['\"](.+?)['\"]", msg)
    if not m:
        return None
    raw = m.group(1)
    fm = re.match(r"<function=([^>]+)>(.+)", raw, re.DOTALL)
    if not fm:
        return None
    name = fm.group(1).strip()
    try:
        args = json.loads(fm.group(2).strip())
    except json.JSONDecodeError:
        args = {}
    return name, args


def _detect_direct_tools(user_query: str) -> list[tuple[str, dict]]:
    """Deterministic tool dispatch for patterns Groq 8b mishandles."""
    q = user_query.lower()
    planned: list[tuple[str, dict]] = []

    compare = _extract_compare_projects(user_query)
    if compare:
        planned.append(("compare_projects", {"project_a": compare[0], "project_b": compare[1]}))

    if any(p in q for p in SUMMARIZE_PATTERNS):
        planned.append(("summarize_conversation", {}))

    if any(p in q for p in LIST_PROJECT_PATTERNS):
        planned.append(("list_projects", {}))

    if any(p in q for p in EDUCATION_PATTERNS):
        planned.append(("search_knowledge_base", {"query": user_query}))

    if any(p in q for p in CONTACT_PATTERNS):
        purpose = "collaboration"
        if "intern" in q:
            purpose = "internship"
        elif "hire" in q or "full-time" in q or "full time" in q:
            purpose = "full-time"
        planned.append(("prepare_contact_draft", {"purpose": purpose}))

    if not planned and any(p in q for p in FAVORITE_PATTERNS):
        search_q = (
            "tell me about TaxSetu my flagship most meaningful project origin story"
            if "flagship" in q
            else "tell me about TaxSetu my most meaningful project origin story"
        )
        planned.append((
            "search_knowledge_base",
            {"query": search_q},
        ))

    if not planned and any(p in q for p in KB_FAST_PATTERNS):
        planned.append(("search_knowledge_base", {"query": user_query}))

    return planned


def _synthesize_from_tools(
    user_query: str,
    tool_payloads: list[dict],
    conversation_history: list | None = None,
) -> str:
    entity_note = ""
    if conversation_history:
        from agents.rag_agent import needs_entity_expansion, extract_last_entity

        if needs_entity_expansion(user_query):
            entity = extract_last_entity(conversation_history)
            if entity:
                entity_note = (
                    f"\nIMPORTANT: The visitor's follow-up refers to {entity}. "
                    f"Answer about {entity} only — do not switch to another project.\n"
                )

    prompt = (
        "You are Tharun (human engineer). Answer in first person from these tool results only. "
        "Never say chatbot, conversational AI, or assistant."
        f"{entity_note}\n\n"
        f"Tool results:\n{json.dumps(tool_payloads, indent=2)[:3000]}\n\n"
        f"Visitor asked: {user_query}\n\nAnswer:"
    )
    return generate_text(prompt, max_tokens=300)


def _execute_tool_batch(
    planned: list[tuple[str, dict]],
    session_id: str,
    conversation_history: list,
    steps: list,
    tools_used: list,
) -> tuple[list[dict], float | None]:
    payloads: list[dict] = []
    best_score: float | None = None

    for name, args in planned:
        _append_step(steps, "tool", f"Executing {name}", tool=name, input=args)
        tools_used.append(name)
        result = _normalize_tool_result(execute_tool(
            name,
            args,
            session_id=session_id,
            conversation_history=conversation_history,
        ))
        if name == "search_knowledge_base" and result.get("ok"):
            score = result.get("data", {}).get("best_score")
            if score is not None:
                best_score = max(best_score or 0, score)
        preview = json.dumps(result.get("data", result))[:200]
        _append_step(steps, "observe", f"{name} returned data", preview=preview)
        payloads.append({"tool": name, "result": result})

    return payloads, best_score


def _run_direct_tools(
    user_query: str,
    session_id: str,
    conversation_history: list,
) -> tuple[str, list, list, float | None, list] | None:
    planned = _detect_direct_tools(user_query)
    if not planned:
        return None

    steps: list = []
    tools_used: list = []
    _append_step(steps, "plan", f"Direct dispatch: {[p[0] for p in planned]}")

    payloads, best_score = _execute_tool_batch(
        planned, session_id, conversation_history, steps, tools_used,
    )

    _append_step(steps, "respond", "Synthesizing from direct tool results")
    text = _synthesize_from_tools(user_query, payloads, conversation_history)
    messages = [{"role": "tool", "content": json.dumps(p)} for p in payloads]
    return text, steps, tools_used, best_score, messages


def _groq_with_tools(messages: list, api_key: str):
    client = Groq(api_key=api_key)
    return client.chat.completions.create(
        model=FAST_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        max_tokens=600,
        temperature=0.2,
    )


def _groq_call_with_recovery(messages: list, groq_keys: list) -> tuple[object | None, tuple[str, dict] | None]:
    """Try Groq tool call; on tool_use_failed, return parsed tool for manual execution."""
    last_exc: Exception | None = None
    for index, key in enumerate(groq_keys):
        try:
            return _groq_with_tools(messages, key), None
        except Exception as exc:
            last_exc = exc
            recovered = _recover_failed_tool_call(exc)
            if recovered:
                return None, recovered
    if last_exc:
        raise last_exc
    return None, None


def _reground_from_tools(user_query: str, messages: list, groq_keys: list) -> str:
    """Re-synthesize strictly from tool outputs when persona drifts."""
    tool_data = [m["content"] for m in messages if m.get("role") == "tool"]
    prompt = (
        "You are Tharun (human engineer). Answer ONLY from these tool results. "
        "First person. Never say chatbot, conversational AI, or assistant.\n\n"
        f"Tool data:\n{chr(10).join(tool_data[-3:])}\n\n"
        f"Question: {user_query}\n\nAnswer:"
    )
    try:
        return generate_text(prompt, max_tokens=250)
    except Exception:
        return (
            "I'm Tharun — agentic AI engineer from India, studying at RGUKT Basar. "
            "I build systems like TaxSetu and NINA. What do you want to dig into?"
        )


def _run_tool_loop(
    user_query: str,
    session_id: str,
    conversation_history: list,
) -> tuple[str, list, list, float | None, list]:
    """
    Returns (final_text, agent_steps, tools_used, best_rag_score, messages).
    """
    direct = _run_direct_tools(user_query, session_id, conversation_history)
    if direct:
        return direct

    steps: list = []
    tools_used: list = []
    best_score: float | None = None

    history_text = ""
    if conversation_history:
        history_text = "\n".join(
            f"{'Visitor' if h['role'] == 'user' else 'Me'}: {h['text']}"
            for h in conversation_history[-4:]
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"{('RECENT CHAT:\\n' + history_text + '\\n\\n') if history_text else ''}"
                f"VISITOR: {user_query}"
            ),
        },
    ]

    _append_step(steps, "plan", "Agent deciding which tools to use")

    groq_keys = get_groq_keys()
    if not groq_keys:
        raise RuntimeError("No Groq API keys for tool agent")

    for _round_num in range(MAX_TOOL_ROUNDS):
        response, recovered = _groq_call_with_recovery(messages, groq_keys)

        if recovered:
            name, args = recovered
            _append_step(steps, "tool", f"Recovered failed call → {name}", tool=name, input=args)
            tools_used.append(name)
            result = _normalize_tool_result(execute_tool(
                name, args, session_id=session_id, conversation_history=conversation_history,
            ))
            preview = json.dumps(result.get("data", result))[:200]
            _append_step(steps, "observe", f"{name} returned data", preview=preview)
            messages.append({"role": "tool", "content": json.dumps(result)})
            if name == "search_knowledge_base" and result.get("ok"):
                score = result.get("data", {}).get("best_score")
                if score is not None:
                    best_score = max(best_score or 0, score)
            continue

        if not response:
            raise RuntimeError("Tool agent LLM failed")

        choice = response.choices[0]
        message = choice.message

        if message.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )

            for tc in message.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                _append_step(
                    steps,
                    "tool",
                    f"Executing {name}",
                    tool=name,
                    input=args,
                )
                tools_used.append(name)

                result = _normalize_tool_result(execute_tool(
                    name,
                    args,
                    session_id=session_id,
                    conversation_history=conversation_history,
                ))

                if name == "search_knowledge_base" and result.get("ok"):
                    data = result.get("data", {})
                    score = data.get("best_score")
                    if score is not None:
                        best_score = max(best_score or 0, score)

                preview = json.dumps(result.get("data", result))[:200]
                _append_step(steps, "observe", f"{name} returned data", preview=preview)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        if message.content:
            _append_step(steps, "respond", "Synthesizing answer from tool results")
            return message.content.strip(), steps, tools_used, best_score, messages

        break

    _append_step(steps, "respond", "Fallback synthesis after tool loop")
    synthesis_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Visitor asked: {user_query}\n"
        f"Tool trace: {json.dumps(steps[-6:])}\n"
        f"Answer as Tharun in first person:"
    )
    text = generate_text(synthesis_prompt, max_tokens=300)
    return text, steps, tools_used, best_score, messages


def tool_agent(state: AgentState) -> AgentState:
    """Run agentic tool loop and return grounded response."""
    try:
        text, steps, tools_used, best_score, loop_messages = _run_tool_loop(
            state["user_query"],
            state.get("session_id", ""),
            state.get("conversation_history") or [],
        )
        text = enforce_persona(text, state["user_query"])
        text = enforce_education_facts(text, state["user_query"])
        text = enforce_contact_email(text)
        if has_persona_violation(text) and tools_used:
            text = enforce_persona(
                _reground_from_tools(state["user_query"], loop_messages, get_groq_keys()),
                state["user_query"],
            )
            text = enforce_education_facts(text, state["user_query"])

        action = detect_action(state["user_query"])
        if "prepare_contact_draft" in tools_used and not action:
            action = detect_action(state["user_query"]) or {
                "type": "open_email",
                "url": "mailto:parsavenkatatharun@gmail.com",
                "label": "Opening email...",
            }

        return {
            **state,
            "final_response": text,
            "response_source": _resolve_response_source(tools_used),
            "rag_grounded": bool(tools_used),
            "rag_score": best_score,
            "agent_steps": steps,
            "tools_used": tools_used,
            "action": action,
        }
    except Exception as exc:
        logger.warning("tool_agent failed, falling back to RAG: %s", exc)
        from agents.rag_agent import rag_agent
        fallback = rag_agent(state)
        if not isinstance(fallback, dict):
            fallback = {}
        if fallback.get("final_response") and fallback.get("response_source") != "fallback":
            return {
                **fallback,
                "agent_steps": [{"type": "fallback", "detail": f"Tool agent error: {exc}"}],
                "tools_used": [],
            }
        return {
            **state,
            "final_response": (
                "Hit a snag running my agent tools — ask me something specific "
                "about a project, or email parsavenkatatharun@gmail.com"
            ),
            "response_source": "fallback",
            "rag_grounded": False,
            "agent_steps": [{"type": "error", "detail": str(exc)}],
            "tools_used": [],
            "error": str(exc),
        }
