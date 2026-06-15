"""
Agent tools — real actions the portfolio agent can take.
Each tool does work (search, compare, summarize) — not canned Q&A strings.
"""
from tools.knowledge_tools import search_knowledge_base
from tools.project_tools import compare_projects, list_projects
from tools.session_tools import summarize_conversation
from tools.contact_tools import prepare_contact_draft

TOOL_REGISTRY = {
    "search_knowledge_base": search_knowledge_base,
    "compare_projects": compare_projects,
    "list_projects": list_projects,
    "summarize_conversation": summarize_conversation,
    "prepare_contact_draft": prepare_contact_draft,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search Tharun's verified knowledge base for facts about identity, "
                "projects, skills, experience, education, philosophy, hackathons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_projects",
            "description": (
                "Compare two of Tharun's projects side-by-side using KB facts. "
                "Use when visitor asks to compare, difference between, vs, or which is better."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_a": {"type": "string"},
                    "project_b": {"type": "string"},
                },
                "required": ["project_a", "project_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "List Tharun's main projects with one-line descriptions from KB.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_conversation",
            "description": (
                "Summarize what has been discussed in this session so far. "
                "Use when visitor asks for recap, summary, or what we talked about."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_contact_draft",
            "description": (
                "Build a contact draft with email/LinkedIn and suggested subject line "
                "for reaching Tharun. Use for hire, collaborate, contact, reach out."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "purpose": {
                        "type": "string",
                        "description": "e.g. internship, full-time, collaboration",
                    },
                },
            },
        },
    },
]


def execute_tool(
    name: str,
    arguments: dict,
    session_id: str = "",
    conversation_history: list | None = None,
) -> dict:
    """Run a tool by name; returns structured result for the agent loop."""
    if not isinstance(arguments, dict):
        arguments = {}
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {"ok": False, "error": f"Unknown tool: {name}"}

    if name == "summarize_conversation":
        arguments = {
            **(arguments if isinstance(arguments, dict) else {}),
            "session_id": session_id,
            "history": conversation_history or [],
        }

    if name == "search_knowledge_base":
        from agents.rag_agent import expand_with_context, needs_entity_expansion, rewrite_query

        query = str(arguments.get("query") or "")
        if conversation_history and needs_entity_expansion(query):
            query = expand_with_context(query, conversation_history)
        else:
            rewritten = rewrite_query(query)
            if rewritten != query:
                query = rewritten
        arguments = {**arguments, "query": query}

    try:
        result = fn(**arguments)
        if result is None:
            result = {}
        if not isinstance(result, dict):
            result = {"value": result}
        return {"ok": True, "data": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
