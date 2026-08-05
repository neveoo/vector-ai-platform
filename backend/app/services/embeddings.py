"""
Embedding generation.

We default to a local sentence-transformers model (BAAI/bge-small-en-v1.5)
rather than an API embedding model, deliberately:
- Zero marginal cost per document, which matters for a self-funded demo.
- No per-tenant data leaving the server for embedding, which is a real
  argument enterprise buyers care about.
- It gives us something concrete to compare against an API model
  (OpenAI/Voyage) in the eval writeup -- see docs/EVALS.md.

The model is loaded once at import time and reused; loading it per
request would be far too slow.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_name)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of chunk strings. Returns one vector per input string."""
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single search/RAG query string using the same model as documents."""
    return embed_texts([query])[0]
