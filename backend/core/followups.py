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
    user_query: str,
    response_text: str,
    intent: str | None,
    conversation_history: list,
    visitor_type: str = "unknown",
) -> list[str]:
    """Return 2-3 follow-up questions based on response content and intent."""
    response_lower = (response_text or "").lower()
    query_lower = (user_query or "").lower()
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

    # Visitor-persona aware prompts improve engagement quality.
    persona_boost = []
    if visitor_type == "recruiter":
        persona_boost = [
            "Would you like my resume and contact details?",
            "Want a quick walkthrough of my flagship project TaxSetu?",
            "Should I summarize my role-fit for Agentic AI Engineer positions?",
        ]
    elif visitor_type == "collaborator":
        persona_boost = [
            "Want to discuss a startup or product idea together?",
            "Should I break down how I design multi-agent systems for real products?",
            "Want to explore collaboration options and next steps?",
        ]
    elif visitor_type == "student":
        persona_boost = [
            "Want a beginner-friendly roadmap to learn agentic AI?",
            "Should I explain my build-first learning process with examples?",
            "Want open-source project recommendations from my GitHub?",
        ]
    elif visitor_type == "engineer":
        persona_boost = [
            "Want a deep dive into my LangGraph orchestration design?",
            "Should I explain my RAG grounding and fallback strategy?",
            "Want architecture-level details on TaxSetu or InfraGenie?",
        ]

    if "flagship" in query_lower or "favorite" in query_lower or "favourite" in query_lower:
        persona_boost.insert(0, "Want the full TaxSetu architecture breakdown (agents + workflow)?")

    asked = {
        msg.get("text", "").lower().strip()
        for msg in conversation_history
        if msg.get("role") == "user"
    }

    ordered = persona_boost + candidates
    filtered = [q for q in ordered if q.lower() not in asked]
    return filtered[:3] if filtered else candidates[:2]
