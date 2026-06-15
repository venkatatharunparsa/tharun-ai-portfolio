"""
Proactive Follow-up Suggestion Engine.
After each response, suggests 2-3 relevant follow-up questions.
"""

FOLLOWUP_MAP = {
    "taxsetu": [
        "What was the hardest technical challenge in TaxSetu?",
        "Who was on the TaxSetu team?",
        "What's the future vision for TaxSetu?",
        "How did TaxSetu perform at KSUM hackathon?",
    ],
    "infragenie": [
        "How did you prevent runaway AWS costs in InfraGenie?",
        "What's the 5-agent architecture in InfraGenie?",
        "What makes InfraGenie different from regular IaC tools?",
    ],
    "nina": [
        "How does NINA understand dynamic website structures?",
        "What was the hardest part of building NINA?",
        "What's the future vision for NINA?",
    ],
    "visionsync": [
        "How did you achieve 95% character consistency?",
        "What is LoRA fine-tuning and why did you use it?",
        "How did VisionSync perform at the Cine AI hackathon?",
    ],
    "careerguide": [
        "Is Career Guide open source?",
        "How does the job matching algorithm work?",
        "What sites does Career Guide scrape?",
    ],
    "astradeploy": [
        "What monitoring tools did you use in AstraDeploy?",
        "How does the CI/CD pipeline work?",
    ],
    "philosophy": [
        "How do you approach a new problem from scratch?",
        "What do you think about AI replacing engineers?",
        "What's your view on system design vs coding?",
    ],
    "skills": [
        "Which of your projects best demonstrates your AI skills?",
        "What are you currently learning?",
        "What's your preferred tech stack?",
    ],
    "experience": [
        "Tell me about your Microsoft Azure internship.",
        "What hackathons have you won?",
        "What certifications do you have?",
    ],
    "contact": [
        "What kind of opportunities are you looking for?",
        "Are you open to remote work?",
        "What's the best way to reach you?",
    ],
    "identity": [
        "Tell me about your most impactful project.",
        "What's your engineering philosophy?",
        "What are you currently working on?",
    ],
    "default": [
        "Tell me about TaxSetu.",
        "What is your engineering philosophy?",
        "How can I contact you?",
    ],
}


def get_followups(
    response_text: str,
    intent: str | None,
    conversation_history: list,
) -> list[str]:
    """Return 2-3 follow-up questions based on response content and intent."""
    response_lower = response_text.lower()
    topic = "default"

    if any(w in response_lower for w in ["taxsetu", "gst", "compliance", "tax filing"]):
        topic = "taxsetu"
    elif any(w in response_lower for w in ["infragenie", "terraform", "infrastructure", "aws"]):
        topic = "infragenie"
    elif any(w in response_lower for w in ["nina", "browser automation", "dom", "playwright"]):
        topic = "nina"
    elif any(w in response_lower for w in ["visionsync", "lora", "film", "storyboard", "character"]):
        topic = "visionsync"
    elif any(w in response_lower for w in ["career guide", "careerguide", "job scraping"]):
        topic = "careerguide"
    elif any(w in response_lower for w in ["astradeploy", "jenkins", "grafana", "mlops"]):
        topic = "astradeploy"
    elif intent in ("philosophy", "about_me") or any(
        w in response_lower for w in ["philosophy", "believe", "approach", "system design"]
    ):
        topic = "philosophy"
    elif intent == "skills" or "skill" in response_lower:
        topic = "skills"
    elif intent == "experience":
        topic = "experience"
    elif intent == "contact":
        topic = "contact"
    elif intent in ("about_me", "small_talk"):
        topic = "identity"

    candidates = FOLLOWUP_MAP.get(topic, FOLLOWUP_MAP["default"])

    asked = {
        msg.get("text", "").lower().strip()
        for msg in conversation_history
        if msg.get("role") == "user"
    }

    filtered = [q for q in candidates if q.lower() not in asked]
    return filtered[:3] if filtered else candidates[:2]
