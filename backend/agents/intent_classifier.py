"""
Intent Classifier Agent — Gate 3 of the Tharun AI pipeline.

Uses Groq LLaMA (fast, cheap) to classify user intent into predefined categories.
This determines which downstream agent handles the query.
"""
import json
from groq import Groq
from agents import AgentState
from config import FAST_MODEL
from core.provider_keys import get_groq_keys, try_with_keys

SMALLTALK_EXACT = {"hi", "hey", "hello", "sup", "howdy", "namaste"}

SMALLTALK_PATTERNS = [
    "good morning", "good afternoon",
    "good evening", "how are you", "what's up", "whats up",
    "nice to meet", "thank you", "thanks",
]

# Route to tool agent (not smalltalk LLM)
AGENT_TOOL_PATTERNS = [
    "summarize", "recap", "what did we talk", "what have we discussed",
    "what we talked", "compare", " vs ", " versus ", "difference between",
    "list your projects", "list projects", "what projects do",
    "who are you", "who is tharun", "tell me about yourself", "about yourself",
]

GITHUB_INTENT_PATTERNS = [
    "how many repos", "repositories do you have", "github activity",
    "languages do you use", "recent commits", "stars on github",
    "open source on github", "most used language", "github stats",
    "show me your github", "github repos", "recent github",
]

CONTACT_PATTERNS = [
    "contact", "email", "reach", "phone", "linkedin", "hire me",
    "get in touch", "how can i reach", "how do i contact",
    "what is your github", "github profile", "github link",
]


def rule_based_intent(query: str) -> str | None:
    """
    Fast rule-based intent detection for obvious patterns.
    Returns intent string or None if Groq classification is needed.
    """
    q = query.lower().strip()
    if any(p in q for p in AGENT_TOOL_PATTERNS):
        return "unknown"
    if any(p in q for p in GITHUB_INTENT_PATTERNS):
        return "github"
    if any(p in q for p in CONTACT_PATTERNS):
        return "contact"
    if q in SMALLTALK_EXACT or q.rstrip("!.?") in SMALLTALK_EXACT:
        return "small_talk"
    if any(p in q for p in SMALLTALK_PATTERNS):
        return "small_talk"
    return None


INTENT_PROMPT = """You are an intent classifier for Tharun AI.

Classify into exactly one of these intents:
- about_me: who is tharun, background, identity
- projects: his projects (TaxSetu, NINA, InfraGenie, VisionSync, AstraDeploy, CareerGuide)
- skills: technical skills, stack, tools
- experience: work experience, hackathons, certifications, Microsoft
- education: studies, university, RGUKT, CGPA
- philosophy: engineering beliefs, approach, opinions on AI
- availability: hiring, collaboration, internship, opportunities
- contact: contact info, email, LinkedIn, GitHub profile link
- github: GitHub repos, languages, activity, stars, open source stats
- small_talk: greetings, casual conversation
- unknown: anything else

Respond ONLY with JSON. No markdown.
{"intent": "<intent>", "confidence": <0.0-1.0>}

Query: """


def intent_classifier_agent(state: AgentState) -> AgentState:
    """
    Classify user intent using Groq LLaMA.
    Fast and cheap — designed for sub-200ms classification.
    """
    try:
        ruled = rule_based_intent(state["user_query"])
        if ruled:
            return {
                **state,
                "intent": ruled,
                "intent_confidence": 1.0,
            }

        def classify_with_key(api_key: str) -> str:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=FAST_MODEL,
                messages=[
                    {"role": "user", "content": INTENT_PROMPT + state["user_query"]}
                ],
                max_tokens=50,
                temperature=0.1,
            )
            return response.choices[0].message.content.strip()

        raw = try_with_keys(get_groq_keys(), "groq-intent", classify_with_key)
        if not raw:
            raise RuntimeError("All Groq keys failed for intent classification")

        parsed = json.loads(raw)
        intent = parsed.get("intent", "unknown")
        confidence = float(parsed.get("confidence", 0.5))

        return {
            **state,
            "intent": intent,
            "intent_confidence": confidence
        }

    except Exception as e:
        return {
            **state,
            "intent": "unknown",
            "intent_confidence": 0.0,
            "error": f"Intent classifier error: {e}"
        }
