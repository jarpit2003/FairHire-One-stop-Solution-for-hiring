"""
embeddings/embedder.py

Previously used Google Gemini text-embedding-004.
Embeddings are now handled locally in services/semantic_matcher.py
using BM25-inspired TF-IDF — no external API required.

This file is kept as a stub so the import in core/routers.py
does not break. The embed_text function is no longer called.
"""
from __future__ import annotations


def embed_text(text: str) -> list[float]:
    """Stub — local TF-IDF in semantic_matcher.py replaced this."""
    raise NotImplementedError(
        "embed_text is no longer used. "
        "Semantic similarity is computed locally in services/semantic_matcher.py"
    )
