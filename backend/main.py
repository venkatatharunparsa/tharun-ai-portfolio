"""
Tharun AI Portfolio — FastAPI Entry Point.
Exposes /chat REST endpoint and /health probe.
WebSocket voice endpoint wired in Phase 3.
"""
import os
import uuid
import sentry_sdk
from fastapi import FastAPI, HTTPException, WebSocket
from voice.websocket_handler import handle_voice_websocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import validate_config, FRONTEND_URL, SENTRY_DSN
from core.fast_path import warmup_fast_path_cache

if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)

validate_config()

app = FastAPI(
    title="Tharun AI Portfolio API",
    description="Agentic voice portfolio backend — Venkata Tharun Parsa",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    warmup_fast_path_cache()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None
    language: str = "en"
    conversation_history: list | None = None


class ChatResponse(BaseModel):
    response: str
    intent: str | None
    response_source: str | None
    rag_score: float | None
    cache_hit: bool
    processing_time_ms: float | None
    session_id: str
    action: dict | None = None
    agent_steps: list | None = None
    tools_used: list | None = None
    followup_suggestions: list[str] = []
    visitor_type: str | None = None


@app.get("/")
async def root():
    return {"agent": "Tharun AI", "status": "online", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/ping")
async def ping():
    return {"status": "pong"}


@app.websocket("/voice")
async def voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice interaction.
    Accepts binary audio chunks, returns TTS audio or web speech signal.
    """
    await handle_voice_websocket(websocket)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts text query, runs through full agent pipeline, returns response.
    """
    try:
        from agents.graph import process_query

        session_id = request.session_id or str(uuid.uuid4())

        from core.followups import get_followups
        from core.visitor_intent import (
            detect_visitor_type,
            get_proactive_message,
            should_send_proactive,
        )

        history = request.conversation_history or []

        result = process_query(
            user_query=request.query,
            session_id=session_id,
            language=request.language,
            conversation_history=history,
        )

        final_response = result.get("final_response") or (
            "I'm not sure how to answer that. Please contact Tharun directly "
            "at parsavenkatatharun@gmail.com"
        )

        visitor_type = detect_visitor_type(history, request.query)
        if should_send_proactive(history, visitor_type):
            proactive = get_proactive_message(visitor_type)
            if proactive:
                final_response = f"{final_response}\n\n{proactive}"

        followups: list[str] = []
        if result.get("response_source") not in ("fallback", "instant"):
            followups = get_followups(
                user_query=request.query,
                response_text=final_response,
                intent=result.get("intent"),
                conversation_history=history,
                visitor_type=visitor_type,
            )

        return ChatResponse(
            response=final_response,
            intent=result.get("intent"),
            response_source=result.get("response_source"),
            rag_score=result.get("rag_score"),
            cache_hit=result.get("cache_hit", False),
            processing_time_ms=result.get("processing_time_ms"),
            session_id=session_id,
            action=result.get("action"),
            agent_steps=result.get("agent_steps"),
            tools_used=result.get("tools_used"),
            followup_suggestions=followups,
            visitor_type=visitor_type,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline error: {str(e)}"
        )
