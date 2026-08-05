"""
Turns raw file bytes into a list of text chunks ready for embedding.

Chunking strategy notes (worth restating in the README/writeup, since
this is one of the things an interviewer will actually probe):
- We chunk by token count (via tiktoken) rather than character count,
  since embedding models and LLM context windows are token-bounded.
- We use overlap between consecutive chunks so a sentence split across
  a chunk boundary isn't lost to retrieval.
- TODO (next iteration): structure-aware chunking that respects
  headings/sections in PDFs and Word docs rather than blind token
  windows -- this measurably improves retrieval precision and is a
  good thing to demo in the eval writeup (before/after recall@k).
"""
from dataclasses import dataclass

import tiktoken

from app.core.config import get_settings

settings = get_settings()
_encoding = tiktoken.get_encoding("cl100k_base")


@dataclass
class ExtractedChunk:
    chunk_index: int
    content: str
    page_number: int | None = None
    section_heading: str | None = None


def extract_text(contents: bytes, mime_type: str) -> str:
    """
    Extract plain text from raw file bytes.
    TODO: wire up real extraction per mime_type:
      - application/pdf -> pypdf or pdfplumber (page numbers matter for citations)
      - .docx -> python-docx
      - text/plain, text/markdown -> decode directly
    """
    if mime_type in ("text/plain", "text/markdown"):
        return contents.decode("utf-8", errors="ignore")
    raise NotImplementedError(f"Text extraction not yet implemented for {mime_type}")


def chunk_text(text: str) -> list[ExtractedChunk]:
    """Token-aware sliding-window chunking with overlap."""
    tokens = _encoding.encode(text)
    chunk_size = settings.chunk_size_tokens
    overlap = settings.chunk_overlap_tokens

    chunks: list[ExtractedChunk] = []
    start = 0
    index = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(ExtractedChunk(chunk_index=index, content=_encoding.decode(chunk_tokens)))
        index += 1
        if end == len(tokens):
            break
        start = end - overlap  # step forward, but re-include the overlap window

    return chunks
