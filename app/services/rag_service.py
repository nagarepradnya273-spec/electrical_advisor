"""
The RAG pipeline (spec section 14): chunk -> embed -> store -> retrieve.
Generation of a grounded answer from retrieved chunks lives separately in
knowledge_ai_service.py, mirroring the split between advisor_service.py
(matching) and ai_service.py (the actual Claude call).
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.services.embedding_service import (
    get_embedding,
    embedding_model_name,
    cosine_similarity,
    build_corpus_idf,
    FALLBACK_MODEL_NAME,
)

CHUNK_SIZE = 700  # characters, not tokens - simple and dependency-free
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Splits on paragraph boundaries first, then packs paragraphs into chunks
    up to chunk_size, so a chunk only ever cuts a sentence in half if a
    single paragraph itself exceeds chunk_size.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(para) > chunk_size:
            step = max(chunk_size - overlap, 1)
            for i in range(0, len(para), step):
                chunks.append(para[i:i + chunk_size])
        else:
            current = para

    if current:
        chunks.append(current)

    return chunks


def _fallback_corpus_idf(db: Session) -> dict:
    """
    IDF table built from EVERY chunk currently stored under the local
    fallback model (see embedding_service.build_corpus_idf). Recomputing
    this from the whole corpus - rather than per document at ingest time -
    is what keeps every fallback-embedded chunk in the same, consistent
    vector space; see _refresh_all_fallback_embeddings for why that matters.
    No-op once Voyage is configured, since real embeddings don't need this.
    """
    rows = db.query(KnowledgeChunk.content).filter(
        KnowledgeChunk.embedding_model == FALLBACK_MODEL_NAME
    ).all()
    return build_corpus_idf([content for (content,) in rows])


def _refresh_all_fallback_embeddings(db: Session) -> None:
    """
    Recomputes IDF over the whole knowledge base and re-embeds every chunk
    stored under the local fallback model. Without this, a document
    ingested early (when few other documents existed yet) would carry
    different IDF weights than one ingested later, making their vectors
    incomparable even though they share the same embedding_model label.
    Cheap at this knowledge base's scale (tens of documents); skipped
    entirely once Voyage is configured (see ingest_document).
    """
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.embedding_model == FALLBACK_MODEL_NAME).all()
    idf = build_corpus_idf([c.content for c in chunks])
    for chunk in chunks:
        chunk.embedding = json.dumps(get_embedding(chunk.content, idf=idf))
    db.commit()


def ingest_document(db: Session, document: KnowledgeDocument) -> int:
    """
    (Re)builds embeddings for a document's chunks under the currently
    active embedding model. Deletes any existing chunks first, so this is
    safe to call again after editing content, or to force a re-embed (see
    the /knowledge/documents/{slug}/reindex route) after changing which
    embedder is configured.
    """
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).delete()

    pieces = chunk_text(document.content)
    model = embedding_model_name()
    for idx, piece in enumerate(pieces):
        db.add(KnowledgeChunk(
            document_id=document.id,
            chunk_index=idx,
            content=piece,
            embedding=json.dumps(get_embedding(piece)),  # provisional under fallback; corrected below
            embedding_model=model,
        ))
    db.commit()

    if model == FALLBACK_MODEL_NAME:
        # Bring this document's new chunks - and every other fallback chunk
        # in the knowledge base - back into a mutually consistent, IDF-
        # weighted vector space (see _refresh_all_fallback_embeddings).
        _refresh_all_fallback_embeddings(db)

    return len(pieces)


def search_knowledge(
    db: Session, query: str, top_k: int = 4, category: Optional[str] = None
) -> list[tuple[KnowledgeChunk, KnowledgeDocument, float]]:
    """
    Returns up to top_k (chunk, document, score) tuples, ranked by cosine
    similarity, highest first.

    Only compares against chunks embedded with the currently active
    embedding model - a chunk embedded by a different model (e.g. Voyage
    embeddings from before a key was removed) has vectors in a different
    space, so comparing them would silently produce meaningless scores
    rather than an error. Call the reindex endpoint after changing
    VOYAGE_API_KEY to bring old chunks back into search.
    """
    model = embedding_model_name()
    idf = _fallback_corpus_idf(db) if model == FALLBACK_MODEL_NAME else None
    query_vector = get_embedding(query, idf=idf)

    q = db.query(KnowledgeChunk).join(KnowledgeDocument).filter(KnowledgeChunk.embedding_model == model)
    if category:
        q = q.filter(KnowledgeDocument.category == category)

    scored = []
    for chunk in q.all():
        vector = json.loads(chunk.embedding)
        score = cosine_similarity(query_vector, vector)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [(chunk, chunk.document, score) for score, chunk in scored[:top_k]]
