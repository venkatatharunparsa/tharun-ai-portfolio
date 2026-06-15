"""
Small Talk Agent — handles greetings and casual conversation.
Uses Gemini Flash with Groq fallback and a strict persona prompt.
"""
import random

from agents import AgentState
from core.generation import generate_text
from core.persona import enforce_persona

INSTANT_GREETINGS = {
    "hi": [
        "Hey! I'm Tharun — I build agentic AI systems. Ask me about my projects or what I'm working on.",
        "Hi there! Tharun here. I work on AI that acts, not just chats. What do you want to know?",
    ],
    "hey": [
        "Hey! I'm Tharun — agentic AI engineer from India. What brings you here?",
        "Hey there! I'm Tharun. Happy to talk projects, skills, or what I'm building lately.",
    ],
    "hello": [
        "Hello! I'm Tharun — I design and ship agentic AI systems. What would you like to explore?",
        "Hi! Tharun here. Ask me about my work, projects, or how I approach engineering.",
    ],
    "sup": [
        "Hey! Tharun here — building agentic AI. What do you want to dig into?",
    ],
    "howdy": [
        "Howdy! I'm Tharun — agentic AI engineer. Ask me anything about my work.",
    ],
    "namaste": [
        "Namaste! I'm Tharun — I build intelligent systems that actually do things. What can I tell you?",
    ],
}

SMALLTALK_PROMPT = """You are Tharun — Venkata Tharun Parsa. An Agentic AI Engineer from India.

When someone greets you or makes small talk:
- Respond naturally like a real person, not a chatbot
- Introduce yourself briefly — who you are and what you do
- Make them curious to ask more
- Keep it 2-3 sentences max
- Vary your responses — don't repeat the same greeting

Examples of good responses:
- "Hey! I'm Tharun — I build agentic AI systems. Ask me about my projects or what I'm working on."
- "Hi there! Tharun here. I work on AI that acts, not just chats. What do you want to know?"
- "Hey, good to meet you. I'm Tharun — agentic AI engineer, builder, and someone who gets way too excited about system design. What brings you here?"

Never say "I am Tharun AI" or describe yourself as a chatbot, virtual assistant, or portfolio agent.
You ARE Tharun — a human engineer. Speak in first person only.

Current message from visitor:"""


def _instant_greeting(query: str) -> str | None:
    normalized = query.lower().strip().rstrip("!.?")
    options = INSTANT_GREETINGS.get(normalized)
    if options:
        return random.choice(options)
    return None


def smalltalk_agent(state: AgentState) -> AgentState:
    """Handle small talk and greetings with persona-driven responses."""
    instant = _instant_greeting(state["user_query"])
    if instant:
        return {
            **state,
            "final_response": instant,
            "response_source": "small_talk",
            "rag_grounded": False,
            "agent_steps": [{"type": "smalltalk", "detail": "Rule-based greeting"}],
            "tools_used": [],
        }

    try:
        answer = enforce_persona(
            generate_text(
                f"{SMALLTALK_PROMPT} {state['user_query']}\n\nRespond naturally:",
                max_tokens=150,
            ),
            state["user_query"],
        )
        return {
            **state,
            "final_response": answer,
            "response_source": "small_talk",
            "rag_grounded": False,
            "agent_steps": [{"type": "smalltalk", "detail": "LLM smalltalk response"}],
            "tools_used": [],
        }

    except Exception as e:
        return {
            **state,
            "final_response": "Hey! I'm Tharun — I build agentic AI systems. Ask me about my projects or what I'm working on.",
            "response_source": "fallback",
            "agent_steps": [{"type": "error", "detail": str(e)}],
            "tools_used": [],
            "error": str(e),
        }
