"""
Central configuration file for Tharun AI Portfolio backend.
All environment variables are loaded here and imported across the app.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load repo-root .env when running from backend/
_root_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_root_env)
load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# LLM Providers (fallback keys used when primary is rate-limited or fails)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_FALLBACK = os.getenv("GEMINI_API_KEY_FALLBACK")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY_FALLBACK = os.getenv("GROQ_API_KEY_FALLBACK")
FAST_MODEL = os.getenv("FAST_MODEL", "llama-3.1-8b-instant")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "models/gemini-2.0-flash-lite")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

# Voice
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3-turbo")
TTS_ELEVENLABS_CHAR_LIMIT = int(os.getenv("TTS_ELEVENLABS_CHAR_LIMIT", "200"))

# Memory
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

# Monitoring
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "tharun-portfolio")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Guardrails — blocked topics for verification_agent
BLOCKED_TOPICS = [
    "salary",
    "politics",
    "religion",
    "medical advice",
    "legal advice",
    "personal relationship",
    "girlfriend",
    "boyfriend",
    "dating",
]

# App Settings
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ADMIN_SECRET = os.getenv("ADMIN_SECRET")

# RAG Settings
RAG_SIMILARITY_THRESHOLD = 0.65
RAG_SIMILARITY_THRESHOLD_SHORT = 0.60
RAG_TOP_K = 5
MAX_RESPONSE_CHARS = 500
MAX_RESPONSE_LENGTH = MAX_RESPONSE_CHARS

LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "20"))
TTS_CHAR_LIMIT = TTS_ELEVENLABS_CHAR_LIMIT
def validate_config():
    required = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY", 
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
