"""

Gemini Embedding API wrapper for knowledge base vectorization.

Tries primary Gemini key, then fallback key.

"""

import google.generativeai as genai



from config import EMBEDDING_MODEL

from core.provider_keys import get_gemini_keys, try_with_keys



EMBEDDING_DIMENSION = 768





def _embed_with_key(text: str, task_type: str, api_key: str) -> list[float]:

    genai.configure(api_key=api_key)

    result = genai.embed_content(

        model=EMBEDDING_MODEL,

        content=text,

        task_type=task_type,

        output_dimensionality=EMBEDDING_DIMENSION,

    )

    return result["embedding"]





def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:

    """

    Generate embedding vector for a text chunk using Gemini Embedding API.

    Returns empty list on failure.

    """

    if not text.strip():

        return []



    keys = get_gemini_keys()

    if not keys:

        return []



    try:

        embedding = try_with_keys(

            keys,

            "gemini-embed",

            lambda key: _embed_with_key(text, task_type, key),

        )

        return embedding or []

    except Exception:

        return []





def embed_query(text: str) -> list[float]:

    """Generate embedding vector optimized for query retrieval."""

    return embed_text(text, task_type="retrieval_query")





def embed_documents(chunks: list[str]) -> list[list[float]]:

    """Batch embed multiple text chunks for document storage."""

    return [embed_text(chunk, task_type="retrieval_document") for chunk in chunks]





def get_embedding(text: str, task_type: str = "retrieval_query") -> list[float]:

    """Generate embedding vector; raises ValueError if all keys fail."""

    embedding = embed_text(text, task_type=task_type)

    if not embedding:

        raise ValueError("Failed to generate embedding")

    return embedding


