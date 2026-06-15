"""
Shared agent state schema for LangGraph orchestration.
All agents in the Tharun AI pipeline use this TypedDict as their state contract.
"""
from typing import TypedDict, Optional, Literal


class AgentState(TypedDict):
    """
    Shared state passed between all agents in the LangGraph pipeline.
    Every agent reads from and writes to this state.
    """
    # Input
    user_query: str                          # Raw text from user (after STT)
    session_id: str                          # Unique session identifier
    language: str                            # Detected language code (en, hi, te, etc.)

    # Verification gate
    verification_status: Literal["pass", "fail", "pending"]
    verification_reason: Optional[str]       # Why it failed (if it did)

    # Intent
    intent: Optional[Literal[
        "about_me",
        "projects",
        "skills",
        "experience",
        "education",
        "contact",
        "philosophy",
        "availability",
        "small_talk",
        "unknown"
    ]]
    intent_confidence: Optional[float]

    # RAG
    retrieved_chunks: Optional[list]         # Top-K chunks from Supabase
    rag_score: Optional[float]               # Best similarity score
    rag_grounded: Optional[bool]             # Did RAG find sufficient context?

    # Response
    final_response: Optional[str]            # Text response to send back
    response_source: Optional[Literal[
        "rag",
        "small_talk",
        "contact_redirect",
        "fallback",
        "cache",
        "instant",
        "agent",
    ]]

    # Agentic (Plan B)
    agent_steps: Optional[list]              # Visible pipeline steps for UI
    tools_used: Optional[list]               # Tool names invoked this turn
    action: Optional[dict]                   # Frontend executable action

    # Voice
    tts_provider: Optional[Literal["elevenlabs", "webspeech", "bhashini"]]
    audio_output: Optional[bytes]            # TTS audio bytes (if generated)

    # Session memory
    conversation_history: Optional[list]     # Last exchanges for RAG context

    # Meta
    cache_hit: bool                          # Was this served from Redis cache?
    error: Optional[str]                     # Any error that occurred
    processing_time_ms: Optional[float]      # Total pipeline time
