"""RAG retrieval quality test."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embeddings import get_embedding
from core.vector_store import search_knowledge
from agents.rag_agent import rewrite_query

test_queries = [
    ("who is tharun", 0.60),
    ("tell me about TaxSetu", 0.65),
    ("tell me about InfraGenie", 0.65),
    ("tell me about VisionSync", 0.65),
    ("tell me about NINA", 0.65),
    ("engineering philosophy", 0.65),
    ("technical skills", 0.65),
    ("hackathon achievements", 0.65),
    ("how to contact tharun", 0.65),
    ("what is your CGPA", 0.60),
]

print("\n=== RAG Retrieval Quality Test ===\n")
failures = []

for query, min_score in test_queries:
    rewritten = rewrite_query(query)
    embedding = get_embedding(rewritten)
    chunks = search_knowledge(embedding, threshold=0.55, top_k=5)

    if not chunks:
        print(f"  FAIL '{query}' -> NO CHUNKS FOUND")
        failures.append(query)
        continue

    best = chunks[0]
    score = best.get("similarity", 0)
    source = best.get("source_file", "unknown")

    status = "PASS" if score >= min_score else "WARN"
    print(f"  {status} '{query}'")
    print(f"     Score: {score:.3f} | Source: {source}")
    print(f"     Preview: {best['content'][:80]}...")
    print()

    if score < min_score:
        failures.append(f"{query} (score {score:.3f} < {min_score})")

print(f"RAG failures: {failures if failures else 'None'}")
