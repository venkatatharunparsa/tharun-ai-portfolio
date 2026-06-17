"""Knowledge base search tool."""
from contextvars import ContextVar

from core.embeddings import get_embedding
from core.vector_store import search_knowledge
from config import (
    RAG_SIMILARITY_THRESHOLD,
    RAG_SIMILARITY_THRESHOLD_SHORT,
    RAG_TOP_K,
)

_request_seen_queries: ContextVar[set[str] | None] = ContextVar(
    "kb_seen_queries", default=None
)


def reset_kb_search_dedup() -> None:
    """Reset per-request KB deduplication state (call at start of each chat turn)."""
    _request_seen_queries.set(set())


def _get_seen_queries() -> set[str]:
    seen = _request_seen_queries.get()
    if seen is None:
        seen = set()
        _request_seen_queries.set(seen)
    return seen


def _adaptive_threshold(query: str) -> float:
    """Short/vague queries need a slightly lower recall threshold."""
    word_count = len((query or "").split())
    return RAG_SIMILARITY_THRESHOLD_SHORT if word_count <= 5 else RAG_SIMILARITY_THRESHOLD


def _query_variants(query: str) -> list[str]:
    """
    Build retrieval variants to improve recall for short/indirect questions.
    Keeps variants small to avoid latency spikes.
    """
    q = (query or "").strip()
    if not q:
        return []

    variants = [q]
    ql = q.lower()

    if "flagship" in ql or "favorite" in ql or "favourite" in ql or "best project" in ql:
        variants.append("TaxSetu flagship project most meaningful project origin story")

    if "what problem" in ql and "solve" in ql:
        variants.append(f"{q} project problem solution impact")

    return list(dict.fromkeys(variants))[:3]


def _fuse_ranked_chunks(rank_lists: list[list[dict]], top_k: int) -> list[dict]:
    """Merge multiple ranked search results by best similarity per chunk text."""
    merged: dict[tuple[str, str], dict] = {}
    for chunks in rank_lists:
        for c in chunks:
            content_key = (c.get("source_file", c.get("source", "unknown")), (c.get("content") or "")[:220])
            existing = merged.get(content_key)
            if not existing or c.get("similarity", 0) > existing.get("similarity", 0):
                merged[content_key] = c
    ranked = sorted(merged.values(), key=lambda x: x.get("similarity", 0), reverse=True)
    return ranked[:top_k]


def search_knowledge_base_deduped(query: str) -> dict:
    """
    Wrapper that prevents duplicate searches for the same query
    within a single agent execution turn.
    """
    seen = _get_seen_queries()
    normalized = (query or "").lower().strip()
    if normalized in seen:
        return {
            "query": query,
            "skipped": True,
            "reason": "duplicate query in same turn",
            "chunk_count": 0,
            "best_score": 0.0,
            "chunks": [],
            "variants_used": [],
        }

    seen.add(normalized)
    return search_knowledge_base(query)


def search_knowledge_base(query: str) -> dict:
    threshold = _adaptive_threshold(query)
    variants = _query_variants(query)

    rank_lists: list[list[dict]] = []
    for variant in variants:
        embedding = get_embedding(variant, task_type="retrieval_query")
        chunks = search_knowledge(
            embedding=embedding,
            threshold=threshold,
            top_k=RAG_TOP_K,
        )
        rank_lists.append(chunks)

    chunks = _fuse_ranked_chunks(rank_lists, RAG_TOP_K)

    if not chunks:
        # Last-chance recall: lower threshold slightly for ambiguous asks.
        for variant in variants[:1]:
            embedding = get_embedding(variant, task_type="retrieval_query")
            chunks = search_knowledge(
                embedding=embedding,
                threshold=max(0.50, threshold - 0.08),
                top_k=RAG_TOP_K,
            )
            if chunks:
                break

    return {
        "query": query,
        "variants_used": variants,
        "chunk_count": len(chunks),
        "best_score": chunks[0]["similarity"] if chunks else 0.0,
        "chunks": [
            {
                "content": c["content"][:800],
                "source": c.get("source_file", c.get("source", "unknown")),
                "score": round(c.get("similarity", 0), 3),
            }
            for c in chunks
        ],
    }
