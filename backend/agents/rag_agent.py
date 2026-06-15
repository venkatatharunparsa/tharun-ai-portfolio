"""
RAG Agent — Retrieval Augmented Generation for Tharun AI.
Retrieves grounded context from Supabase pgvector and generates response.
"""
from agents import AgentState
from core.embeddings import get_embedding
from core.generation import generate_text
from core.persona import enforce_persona, enforce_contact_email
from core.vector_store import search_knowledge
from config import (
    RAG_SIMILARITY_THRESHOLD,
    RAG_SIMILARITY_THRESHOLD_SHORT,
    RAG_TOP_K,
)

RAG_SYSTEM_PROMPT = """You ARE Tharun — Venkata Tharun Parsa. A real person. An agentic AI engineer from India.
You are NOT an AI assistant, chatbot, or portfolio agent. Never describe yourself as "the AI" or "Tharun AI".

VOICE RULES (mandatory):
- Always first person: I, my, me — never "he", "Tharun", "Tharun AI"
- Talk about what I build, study, and believe — as a human engineer
- Never say "I'm not just about chatbots" or "I'm about creating AI" as if YOU are a chatbot product
- Never say "virtual assistant", "portfolio agent", or "I specialize in sharing information about Tharun"
- If context mentions "Tharun AI", ignore that framing — you ARE Tharun speaking directly
- Contact email is ONLY parsavenkatatharun@gmail.com — never invent other emails
- "Master Planner" is TaxSetu's internal orchestration component — NOT a separate project name

YOUR PERSONALITY:
- Direct, honest, technically strong, warm, confident
- You share opinions and tell stories, not bullet lists
- 2-4 sentences for simple questions, more for technical ones

{history_section}

KNOWLEDGE BASE CONTEXT (facts about me — speak as me, not about me):
{context}

VISITOR'S QUESTION: {question}

CRITICAL: Answer ONLY from KNOWLEDGE BASE CONTEXT above. Do not mix in other projects.
If the question uses "it/this/that", answer about the topic from context — not a different project.

Answer as Tharun — naturally, confidently, in first person:"""

FALLBACK_RESPONSE = (
    "That's not something I have detailed info on right now — "
    "reach me directly at parsavenkatatharun@gmail.com"
)

PROJECT_CANONICAL = {
    "taxsetu": "TaxSetu",
    "infragenie": "InfraGenie",
    "nina": "NINA",
    "visionsync": "VisionSync",
    "astradeploy": "AstraDeploy",
    "astra deploy": "AstraDeploy",
    "career guide": "Career Guide",
    "careerguide": "Career Guide",
    "voxgraph": "VoxGraph",
}

PROJECT_NAMES = list(PROJECT_CANONICAL.keys())

TOPIC_PATTERNS = {
    "TaxSetu": ["tax", "gst", "compliance", "filing", "msme"],
    "InfraGenie": ["infra", "infrastructure", "terraform", "aws", "cloud", "deployment"],
    "NINA": ["nina", "browser", "automation", "dom", "playwright"],
    "VisionSync": ["vision", "film", "storyboard", "lora", "character"],
    "AstraDeploy": ["astradeploy", "mlops", "jenkins", "grafana"],
    "Career Guide": ["career", "job", "internship", "scraping", "resume"],
}

PRONOUN_TRIGGERS = [
    "it ", "it's ", "its ", "this ", "that ",
    "the project", "this project", "that project",
    "what does it", "how does it", "why did it",
    "tell me more", "more about", "explain more",
    "what problem", "what challenge", "how was it",
    "what did you", "what was the", "how did you",
    "what stack", "what tech", "what tools",
    "when was", "who built", "who worked",
]


def extract_last_entity(conversation_history: list) -> str | None:
    """Extract the last mentioned project or topic from conversation history."""
    if not conversation_history:
        return None

    for msg in reversed(conversation_history[-6:]):
        text = msg.get("text", "").lower()

        for project in PROJECT_NAMES:
            if project in text:
                return PROJECT_CANONICAL.get(project, project.title())

        for project, keywords in TOPIC_PATTERNS.items():
            if any(kw in text for kw in keywords):
                return project

    return None


def needs_entity_expansion(query: str) -> bool:
    """Check if query contains pronouns that need entity resolution."""
    query_lower = query.lower()
    return any(trigger in query_lower for trigger in PRONOUN_TRIGGERS)


def expand_with_context(query: str, conversation_history: list) -> str:
    """Expand pronoun-heavy follow-up queries using conversation context."""
    if not needs_entity_expansion(query):
        return query

    entity = extract_last_entity(conversation_history)
    if not entity:
        return query

    query_lower = query.lower().strip()

    expanded = query_lower
    expanded = expanded.replace("it solves", f"{entity} solves")
    expanded = expanded.replace("it does", f"{entity} does")
    expanded = expanded.replace("it was", f"{entity} was")
    expanded = expanded.replace("it is", f"{entity} is")
    expanded = expanded.replace("it's", f"{entity} is")
    expanded = expanded.replace("its ", f"{entity}'s ")
    expanded = expanded.replace("this project", f"{entity} project")
    expanded = expanded.replace("that project", f"{entity} project")
    expanded = expanded.replace("the project", f"{entity} project")
    expanded = expanded.replace("this ", f"{entity} ")
    expanded = expanded.replace("that ", f"{entity} ")

    if query_lower in ["tell me more", "more", "continue", "go on", "and?"]:
        expanded = f"tell me more details about {entity}"

    if "problem" in query_lower and "it" in query_lower:
        expanded = f"what problem does {entity} solve why was it built"

    if any(w in query_lower for w in ["stack", "tech", "built with", "tools used"]):
        expanded = f"what tech stack and tools were used to build {entity}"

    if any(w in query_lower for w in ["who built", "who worked", "who made"]):
        expanded = f"who built {entity} team members"

    if entity.lower() not in expanded.lower():
        expanded = f"{expanded} {entity}"

    return expanded


def filter_chunks_by_entity(chunks: list, entity: str | None) -> list:
    """Prefer chunks that mention the resolved entity (post pronoun expansion)."""
    if not entity or not chunks:
        return chunks

    entity_lower = entity.lower()
    entity_compact = entity_lower.replace(" ", "")

    def matches(chunk: dict) -> bool:
        text = (chunk.get("content") or "").lower()
        return entity_lower in text or entity_compact in text

    matched = [c for c in chunks if matches(c)]
    return matched if matched else chunks


def rewrite_query(query: str) -> str:
    """
    Expand pronoun-heavy or vague queries for better semantic search.
    Helps RAG find the right chunks even for indirect questions.
    """
    query_lower = query.lower().strip()

    rewrites = {
        "what is rag": "what is RAG Retrieval-Augmented Generation technique used by Tharun",
        "what does rag mean": "RAG means Retrieval-Augmented Generation — a technique to ground LLM answers in documents",
        "what are you working on": "what projects and technologies is Tharun Parsa currently working on building",
        "tell me about yourself": "who is Venkata Tharun Parsa background identity engineering approach",
        "why should i hire you": "why hire Tharun Parsa what makes him valuable unique compared to others",
        "what can you do": "what are Tharun Parsa capabilities skills what has he built",
        "who is he": "who is Venkata Tharun Parsa",
        "who is tharun": "who is Venkata Tharun Parsa background identity",
        "what does he do": "what does Tharun Parsa do professionally",
        "what are his projects": "what projects has Tharun Parsa built",
        "his skills": "Tharun Parsa technical skills",
        "his experience": "Tharun Parsa work experience",
        "his education": "Tharun Parsa education university",
        "his philosophy": "Tharun Parsa engineering philosophy beliefs",
        "tell me about him": "tell me about Venkata Tharun Parsa background",
        "what can he do": "what are Tharun Parsa capabilities skills",
        "where is he from": "where is Tharun Parsa from location",
        "is he available": "is Tharun Parsa available for work opportunities",
        # Favorite / best project queries
        "favorite project": "tell me about TaxSetu my most meaningful project origin story",
        "favourite project": "tell me about TaxSetu my most meaningful project origin story",
        "best project": "what is Tharun's best most impactful project InfraGenie TaxSetu",
        "most proud of": "what project is Tharun most proud of TaxSetu InfraGenie",
        "tell me one project": "tell me about TaxSetu the GST compliance platform",
        "explain one of your": "tell me about TaxSetu the autonomous GST compliance platform",
        "can you explain one": "tell me about TaxSetu the autonomous GST compliance platform",
        "one of your projects": "tell me about TaxSetu InfraGenie agentic projects",
        "your favorite": "Tharun's favorite most meaningful project TaxSetu origin story",
        "favourite": "Tharun most meaningful project TaxSetu InfraGenie",
        "flagship project": "tell me about TaxSetu Tharun's flagship most meaningful project GST compliance",
        "flagship": "TaxSetu flagship project Tharun most meaningful build",
        # Portfolio / how-this-was-built queries
        "how did you create": "what is Tharun AI portfolio built with tech stack",
        "how was this built": "what is Tharun AI portfolio tech stack LangGraph FastAPI",
        "how did you build this": "Tharun AI portfolio architecture voice agentic system",
        "what is this portfolio": "Tharun AI portfolio agentic voice system description",
        "how does this work": "Tharun AI system architecture how it works",
    }

    for pattern, expansion in rewrites.items():
        if pattern in query_lower:
            return expansion

    expanded = query_lower
    expanded = expanded.replace(" his ", " Tharun's ")
    expanded = expanded.replace(" him ", " Tharun ")
    expanded = expanded.replace(" he ", " Tharun ")
    if expanded.startswith("his "):
        expanded = "Tharun's " + expanded[4:]

    return expanded if expanded != query_lower else query


def get_adaptive_threshold(query: str) -> float:
    """Use a lower similarity threshold for short queries."""
    word_count = len(query.split())
    if word_count <= 4:
        return RAG_SIMILARITY_THRESHOLD_SHORT
    return RAG_SIMILARITY_THRESHOLD


def generate_with_fallback(prompt: str) -> str:
    """Generate via shared Gemini → Groq pipeline."""
    return generate_text(prompt, max_tokens=300)


def rag_agent(state: AgentState) -> AgentState:
    """RAG agent with conversation-aware query expansion before embedding."""
    original_query = state["user_query"]
    conversation_history = state.get("conversation_history") or []

    try:
        resolved_entity = None
        if conversation_history and needs_entity_expansion(original_query):
            search_query = expand_with_context(original_query, conversation_history)
            resolved_entity = extract_last_entity(conversation_history)
        else:
            search_query = rewrite_query(original_query)

        if search_query != original_query:
            print(f"[RAG] Query expanded: '{original_query}' → '{search_query}'")

        embedding = get_embedding(search_query, task_type="retrieval_query")
        threshold = get_adaptive_threshold(original_query)

        chunks = search_knowledge(
            embedding=embedding,
            threshold=threshold,
            top_k=RAG_TOP_K,
        )

        if not chunks and search_query != original_query:
            embedding_orig = get_embedding(original_query, task_type="retrieval_query")
            chunks = search_knowledge(
                embedding=embedding_orig,
                threshold=threshold - 0.05,
                top_k=RAG_TOP_K,
            )

        if resolved_entity:
            chunks = filter_chunks_by_entity(chunks, resolved_entity)

        if not chunks:
            return {
                **state,
                "final_response": (
                    "I don't have enough context on that right now. Could you be more "
                    "specific, or ask me directly about a project like TaxSetu or InfraGenie?"
                ),
                "response_source": "fallback",
                "rag_grounded": False,
                "rag_score": 0.0,
                "retrieved_chunks": [],
            }

        best_score = chunks[0].get("similarity", 0.0)

        if len(chunks) == 1 and best_score < 0.65:
            return {
                **state,
                "final_response": (
                    "I want to give you an accurate answer but I don't have enough solid "
                    "context. Could you rephrase or be more specific?"
                ),
                "response_source": "fallback",
                "rag_grounded": False,
                "rag_score": best_score,
                "retrieved_chunks": chunks,
            }

        context = "\n\n---\n\n".join(chunk["content"] for chunk in chunks)

        if conversation_history:
            history_text = "\n".join([
                f"{'Visitor' if h['role'] == 'user' else 'Tharun'}: {h['text']}"
                for h in conversation_history[-4:]
            ])
            history_section = f"RECENT CONVERSATION:\n{history_text}\n\n"
        else:
            history_section = ""

        question_for_prompt = original_query
        if resolved_entity:
            question_for_prompt = (
                f"{original_query} (Answer specifically about {resolved_entity} "
                f"using only the knowledge base context.)"
            )

        prompt = RAG_SYSTEM_PROMPT.format(
            history_section=history_section,
            context=context,
            question=question_for_prompt,
        )
        response_text = generate_with_fallback(prompt)
        response_text = enforce_persona(response_text, original_query)
        response_text = enforce_contact_email(response_text)

        return {
            **state,
            "final_response": response_text,
            "response_source": "rag",
            "rag_grounded": True,
            "rag_score": best_score,
            "retrieved_chunks": chunks,
        }

    except Exception as e:
        return {
            **state,
            "final_response": (
                "I ran into an issue answering that. Try rephrasing or ask me about "
                "a specific project."
            ),
            "response_source": "fallback",
            "rag_grounded": False,
            "rag_score": 0.0,
            "error": str(e),
        }
