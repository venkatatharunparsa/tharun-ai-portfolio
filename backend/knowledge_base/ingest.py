"""
Knowledge Base Ingestion Pipeline — Tharun AI Portfolio.

Loads markdown documents, splits them into semantic chunks,
generates Gemini embeddings, and upserts into Supabase pgvector.

Chunking strategy:
- Split on markdown headers (##, ###) for semantic boundaries
- Further split long sections by paragraph if > 400 chars
- Overlap: 50 chars between chunks to preserve context
"""
import sys
import time
import re
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from core.embeddings import get_embedding
from core.vector_store import upsert_chunks, clear_all_chunks
from config import validate_config

DOCUMENTS_DIR = Path(__file__).parent / "documents"
MAX_CHUNK_SIZE = 400   # characters
MIN_CHUNK_SIZE = 50    # ignore tiny fragments
OVERLAP = 50           # character overlap between chunks


def split_by_headers(text: str, source_file: str) -> list[dict]:
    """
    Split markdown text into chunks at ## and ### header boundaries.
    Each header section becomes one or more chunks.
    """
    sections = re.split(r'\n(?=#{1,3} )', text.strip())
    chunks = []

    for section in sections:
        section = section.strip()
        if len(section) < MIN_CHUNK_SIZE:
            continue

        if len(section) <= MAX_CHUNK_SIZE:
            chunks.append({
                "content": section,
                "source_file": source_file,
                "metadata": {"type": "section"}
            })
        else:
            paragraphs = [p.strip() for p in section.split('\n\n') if p.strip()]
            current_chunk = ""

            for para in paragraphs:
                if len(current_chunk) + len(para) <= MAX_CHUNK_SIZE:
                    current_chunk += "\n\n" + para if current_chunk else para
                else:
                    if current_chunk and len(current_chunk) >= MIN_CHUNK_SIZE:
                        chunks.append({
                            "content": current_chunk,
                            "source_file": source_file,
                            "metadata": {"type": "paragraph"}
                        })
                    overlap_text = current_chunk[-OVERLAP:] if len(current_chunk) > OVERLAP else current_chunk
                    current_chunk = overlap_text + "\n\n" + para if overlap_text else para

            if current_chunk and len(current_chunk) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "content": current_chunk,
                    "source_file": source_file,
                    "metadata": {"type": "paragraph"}
                })

    return chunks


def load_documents() -> list[dict]:
    """Load markdown documents — exclude guardrails from RAG."""
    EXCLUDE_FROM_RAG = {"guardrails.md", "07_guardrails.md"}

    docs = []
    for md_file in sorted(DOCUMENTS_DIR.glob("*.md")):
        if md_file.name in EXCLUDE_FROM_RAG:
            print(f"  Skipped (excluded from RAG): {md_file.name}")
            continue
        content = md_file.read_text(encoding="utf-8")
        docs.append({
            "filename": md_file.name,
            "content": content
        })
        print(f"  Loaded: {md_file.name} ({len(content)} chars)")
    return docs


def ingest_all():
    """
    Main ingestion pipeline:
    1. Load all markdown documents
    2. Split into semantic chunks
    3. Embed each chunk with Gemini
    4. Upsert into Supabase pgvector
    """
    validate_config()
    print("\n=== Tharun AI — Knowledge Base Ingestion ===\n")

    print("Loading documents...")
    docs = load_documents()
    print(f"  Total documents: {len(docs)}\n")

    print("Chunking documents...")
    all_chunks = []
    for doc in docs:
        chunks = split_by_headers(doc["content"], doc["filename"])
        print(f"  {doc['filename']}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\n  Total chunks to embed: {len(all_chunks)}\n")

    print("Wiping all existing chunks for clean re-ingest...")
    clear_all_chunks()
    time.sleep(2)

    print("Embedding and upserting chunks...")
    inserted = 0
    errors = []

    for i, chunk in enumerate(all_chunks):
        try:
            print(f"  [{i+1}/{len(all_chunks)}] Embedding chunk from {chunk['source_file']}...")

            embedding = get_embedding(chunk["content"], task_type="retrieval_document")

            upsert_chunks([{
                "content": chunk["content"],
                "embedding": embedding,
                "source_file": chunk["source_file"],
                "chunk_index": i,
                "metadata": chunk["metadata"]
            }])

            inserted += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"  ERROR on chunk {i}: {e}")
            errors.append({"chunk": i, "error": str(e)})

    print(f"\n=== Ingestion Complete ===")
    print(f"  Documents: {len(docs)}")
    print(f"  Chunks inserted: {inserted}")
    print(f"  Errors: {len(errors)}")
    if errors:
        print(f"  Error details: {errors}")

    return {
        "documents": len(docs),
        "chunks_inserted": inserted,
        "errors": errors
    }


if __name__ == "__main__":
    result = ingest_all()
    print(f"\nFinal: {result}")
