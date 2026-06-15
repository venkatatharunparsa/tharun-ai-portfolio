# Tharun AI — Agentic Voice Portfolio

A production-grade agentic voice-powered personal portfolio for Venkata Tharun Parsa — Agentic AI Engineer.

## What This Is
Not a website. A live AI agent system. Visitors speak or type — Tharun AI responds with verified, grounded information about Tharun's projects, skills, and experience.

## Stack
- **Frontend:** Next.js 14 + TailwindCSS → Vercel
- **Backend:** FastAPI → Render.com
- **Agents:** LangGraph multi-agent orchestration
- **LLMs:** Gemini 1.5 Flash + Groq LLaMA 3.1
- **Voice:** Groq Whisper (STT) + ElevenLabs (TTS)
- **Vector DB:** Supabase pgvector
- **Memory:** Upstash Redis
- **Monitoring:** LangSmith + Sentry

## Setup
1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your keys
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
4. Frontend: `cd frontend && npm install && npm run dev`

## Architecture
See `/docs/architecture.md` for full system design.
