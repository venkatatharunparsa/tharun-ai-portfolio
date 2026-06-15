"""Knowledge base search tool."""
from core.embeddings import get_embedding
from core.vector_store import search_knowledge
from config import RAG_SIMILARITY_THRESHOLD, RAG_TOP_K


def search_knowledge_base(query: str) -> dict:
    embedding = get_embedding(query, task_type="retrieval_query")
    chunks = search_knowledge(
        embedding=embedding,
        threshold=RAG_SIMILARITY_THRESHOLD,
        top_k=RAG_TOP_K,
    )
    return {
        "query": query,
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
