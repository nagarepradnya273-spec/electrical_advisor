"""
Embedding layer for the RAG knowledge base (spec sections 14, 41).

Same optional-key-with-fallback philosophy as ai_service.py: when
VOYAGE_API_KEY is set, real embeddings come from Voyage AI (Anthropic's
recommended embeddings partner - Claude itself has no embeddings endpoint).
When it isn't set, or the call fails for any reason, a deterministic local
fallback embedding is used instead, so knowledge ingestion and search work
fully with zero paid API keys, exactly like the Advisor does without
ANTHROPIC_API_KEY.

The fallback is a sparse TF-IDF vector (token -> weight), not a trained
model - it ranks chunks by *lexical* overlap with the query, weighted so
distinctive words (e.g. 'capacitor', 'RCBO') count for more than words
common across the whole knowledge base (e.g. 'check', 'warranty'). It has
no notion of synonyms ('AC' vs 'air conditioner' are unrelated tokens to
it) - that's exactly what real embeddings (Voyage) add. This mirrors the
tradeoff ai_service.py makes for problem matching (AI first, keyword
fallback second): the fallback keeps the app fully functional with zero
setup, real embeddings make it meaningfully smarter.
"""
import math
import re
from collections import Counter
from typing import Optional, Union

import httpx

from app.config import settings

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-3-lite"

FALLBACK_MODEL_NAME = "local-tfidf-v1"

# Sparse vector: token -> weight. Dense vector (from Voyage): list[float].
SparseVector = dict
Vector = Union[list, SparseVector]

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "and", "or", "but", "if", "then",
    "this", "that", "these", "those", "it", "its", "with", "as", "by",
    "from", "about", "into", "than", "so", "such", "not", "no", "do",
    "does", "did", "my", "your", "i", "you", "we", "they", "he", "she",
    "can", "will", "should", "would", "what", "which", "when", "how",
}


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def build_corpus_idf(documents: list[str]) -> dict[str, float]:
    """
    Standard inverse-document-frequency weights computed over a corpus of
    texts (typically every existing knowledge chunk). Used only by the
    local fallback embedding: without this, a bag-of-words treats a word
    like 'warranty' or 'circuit' (common across most documents in this
    knowledge base) the same as a distinctive word like 'capacitor' or
    'sweep' - which lets generic vocabulary overlap dominate similarity
    scores. Weighting each token by log(N / how many chunks contain it)
    fixes that: common words shrink toward a low weight, rare/distinctive
    words keep close to full weight.
    """
    doc_count = len(documents)
    if doc_count == 0:
        return {}

    doc_freq: Counter = Counter()
    for text in documents:
        for token in set(_tokenize(text)):
            doc_freq[token] += 1

    return {token: math.log((doc_count + 1) / (freq + 1)) + 1.0 for token, freq in doc_freq.items()}


def _fallback_embedding(text: str, idf: Optional[dict[str, float]] = None) -> SparseVector:
    """
    Deterministic, dependency-free 'embedding': a sparse TF-IDF vector
    keyed directly by token (no hashing - this knowledge base is small
    enough that there's no need to fold the vocabulary into fixed
    buckets, and doing so only introduces collision noise), L2-normalised.
    """
    counts = Counter(_tokenize(text))
    weighted = {token: count * (idf.get(token, 1.0) if idf else 1.0) for token, count in counts.items()}

    norm = math.sqrt(sum(w * w for w in weighted.values()))
    if norm > 0:
        weighted = {token: w / norm for token, w in weighted.items()}
    return weighted


def _voyage_embedding(text: str) -> Optional[list[float]]:
    if not settings.VOYAGE_API_KEY:
        return None
    try:
        response = httpx.post(
            VOYAGE_API_URL,
            headers={
                "Authorization": f"Bearer {settings.VOYAGE_API_KEY}",
                "content-type": "application/json",
            },
            json={"input": [text], "model": VOYAGE_MODEL, "input_type": "document"},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception:
        return None  # caller falls back to the local embedding


def embedding_model_name() -> str:
    """The model that get_embedding() will actually use right now, given
    current settings. Chunks store this so search can compare like-for-like
    (see rag_service.search_knowledge)."""
    return VOYAGE_MODEL if settings.VOYAGE_API_KEY else FALLBACK_MODEL_NAME


def get_embedding(text: str, idf: Optional[dict[str, float]] = None) -> Vector:
    """
    Always returns a vector - never raises. Tries Voyage first when
    configured (returns a dense list[float]), silently falls back
    otherwise (returns a sparse dict[str, float]), so ingestion/search
    never break because an external embeddings API is unset, slow, or down.

    idf is only used by the fallback path (see build_corpus_idf) - pass
    the same idf table to every call within one ingest/search operation so
    all vectors being compared were weighted consistently.
    """
    vector = _voyage_embedding(text)
    if vector is not None:
        return vector
    return _fallback_embedding(text, idf=idf)


def cosine_similarity(a: Vector, b: Vector) -> float:
    """Handles both dense vectors (list[float], from Voyage) and sparse
    vectors (dict[str, float], from the local fallback) - a chunk's
    embedding and the query's embedding are always the same shape in
    practice, since search_knowledge only ever compares vectors produced
    by the same embedding model."""
    if isinstance(a, dict) or isinstance(b, dict):
        if not isinstance(a, dict) or not isinstance(b, dict):
            return 0.0
        keys = a.keys() & b.keys()
        if not keys:
            return 0.0
        dot = sum(a[k] * b[k] for k in keys)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    if len(a) != len(b) or not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
