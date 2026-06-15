"""
Supabase pgvector store for knowledge base retrieval.
"""
import logging
from typing import TypedDict

from supabase import create_client, Client

from config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    RAG_TOP_K,
    RAG_SIMILARITY_THRESHOLD,
)

logger = logging.getLogger(__name__)


class VectorMatch(TypedDict):
    """Single vector search result."""

    content: str
    source: str
    score: float


def _get_client() -> Client | None:
    """Create Supabase client or return None if credentials missing."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_client() -> Client | None:
    """Public accessor for Supabase client."""
    return _get_client()


def clear_document_chunks(source_file: str) -> None:
    """
    Delete all existing chunks for a given source file before re-ingestion.
    Prevents duplicate chunks on re-runs.
    """
    try:
        client = get_supabase_client()
        if not client:
            return
        client.table("knowledge_chunks").delete().eq("source_file", source_file).execute()
    except Exception as e:
        logger.warning("Could not clear chunks for %s: %s", source_file, e)


def search_knowledge(
    embedding: list[float],
    threshold: float = RAG_SIMILARITY_THRESHOLD,
    top_k: int = RAG_TOP_K,
) -> list[dict]:
    """
    Search pgvector and return chunks with similarity scores.
    Used by the RAG agent pipeline.
    """
    results = search_similar(embedding, top_k=top_k, threshold=threshold)
    return [
        {
            "content": row["content"],
            "source_file": row["source"],
            "similarity": row["score"],
        }
        for row in results
    ]


def search_similar(
    query_embedding: list[float],
    top_k: int = RAG_TOP_K,
    threshold: float = RAG_SIMILARITY_THRESHOLD,
) -> list[VectorMatch]:
    """
    Search pgvector for chunks similar to the query embedding.
    Returns ranked matches with similarity scores above threshold.
    """
    try:
        client = _get_client()
        if not client or not query_embedding:
            return []

        result = client.rpc(
            "match_knowledge",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": top_k,
            },
        ).execute()

        return [
            {
                "content": row["content"],
                "source": row["source_file"] or "unknown",
                "score": float(row["similarity"]),
            }
            for row in (result.data or [])
        ]
    except Exception:
        return []


def clear_all_chunks() -> None:
    """
    Wipe entire knowledge_chunks table before clean re-ingest.
    Only call this before a full re-ingest — never in production flow.
    """
    try:
        client = get_supabase_client()
        if not client:
            raise RuntimeError("Supabase client unavailable")
        client.table("knowledge_chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("All chunks cleared from Supabase.")
    except Exception as e:
        logger.error("Clear failed: %s", e)
        raise


def upsert_chunks(chunks: list[dict]) -> bool:
    """
    Insert knowledge base chunks with embeddings into Supabase.
    Returns True on success, False on failure.
    """
    try:
        client = _get_client()
        if not client or not chunks:
            return False
        client.table("knowledge_chunks").insert(chunks).execute()
        return True
    except Exception:
        return False


def count_chunks() -> int:
    """
    Return total number of chunks stored in Supabase.
    Returns 0 on failure.
    """
    try:
        client = _get_client()
        if not client:
            return 0
        result = client.table("knowledge_chunks").select("id", count="exact").execute()
        return result.count or 0
    except Exception:
        return 0
