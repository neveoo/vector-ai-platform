"""
Retrieval-augmented generation.

Two functions, deliberately kept separate:
- semantic_search: pure retrieval, useful standalone (a "search my
  documents" feature) and as a building block for RAG.
- answer_question: retrieval + a grounded LLM answer, with citations
  back to the specific chunks used, and an explicit refusal path when
  retrieval confidence is too low -- this is the piece that separates
  a real RAG implementation from a demo that hallucinates confidently.
"""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embeddings import embed_query

settings = get_settings()

# Below this cosine similarity, we don't trust the retrieved context
# enough to let the model answer from it. Tune this against your eval
# set (docs/EVALS.md) rather than picking it arbitrarily.
MIN_RELEVANCE_SCORE = 0.35


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    similarity: float
    page_number: int | None


def semantic_search(db: Session, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """
    RLS on the session (see set_tenant_context) means this query can
    only ever return chunks belonging to the caller's tenant -- no
    tenant_id filter needed here in application code.
    """
    query_vector = embed_query(query)
    k = top_k or settings.retrieval_top_k

    # cosine_distance (<=>) returns 0 = identical, 2 = opposite;
    # we convert to a similarity score (1 - distance) for readability.
    stmt = (
        select(
            DocumentChunk,
            Document.filename,
            (1 - DocumentChunk.embedding.cosine_distance(query_vector)).label("similarity"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(k)
    )
    rows = db.execute(stmt).all()

    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=filename,
            content=chunk.content,
            similarity=float(similarity),
            page_number=chunk.page_number,
        )
        for chunk, filename, similarity in rows
    ]


def answer_question(db: Session, question: str) -> dict:
    """
    Returns {"answer": str, "citations": [...], "grounded": bool}.
    When nothing retrieved clears MIN_RELEVANCE_SCORE, we explicitly
    decline rather than let the model guess -- this should show up as
    a deliberate, tested behavior in the eval writeup, not an accident.
    """
    retrieved = semantic_search(db, question)
    strong_matches = [r for r in retrieved if r.similarity >= MIN_RELEVANCE_SCORE]

    if not strong_matches:
        return {
            "answer": "I couldn't find anything in your documents relevant enough to answer that confidently.",
            "citations": [],
            "grounded": False,
        }

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    context_block = "\n\n".join(
        f"[Source {i+1}: {r.filename}]\n{r.content}" for i, r in enumerate(strong_matches)
    )
    prompt = (
        "Answer the question using ONLY the sources below. Cite sources as [Source N]. "
        "If the sources don't fully answer the question, say so explicitly rather than guessing.\n\n"
        f"Sources:\n{context_block}\n\nQuestion: {question}"
    )
    response = client.messages.create(
        model=settings.chat_model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "answer": response.content[0].text,
        "citations": [
            {"document_id": str(r.document_id), "filename": r.filename, "similarity": round(r.similarity, 3)}
            for r in strong_matches
        ],
        "grounded": True,
    }
