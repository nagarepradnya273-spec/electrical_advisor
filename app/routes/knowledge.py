from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeDocumentOut,
    KnowledgeDocumentDetailOut,
    KnowledgeDocumentCreate,
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSourceOut,
)
from app.services.rag_service import ingest_document, search_knowledge
from app.services.knowledge_ai_service import generate_grounded_answer

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# Relevance below this is treated as "not actually relevant". With the
# sparse TF-IDF fallback, a truly unrelated query scores exactly 0 (no
# shared vocabulary at all), so this floor mainly guards against weak,
# partial-overlap matches rather than hash-collision noise.
RELEVANCE_FLOOR = 0.1


@router.get("/documents", response_model=List[KnowledgeDocumentOut])
def list_documents(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(KnowledgeDocument)
    if category:
        q = q.filter(KnowledgeDocument.category == category)
    return q.order_by(KnowledgeDocument.title).all()


@router.get("/documents/{slug}", response_model=KnowledgeDocumentDetailOut)
def get_document(slug: str, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return doc


@router.post("/documents", response_model=KnowledgeDocumentOut, status_code=201)
def create_document(
    payload: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="A document with this slug already exists")
    doc = KnowledgeDocument(**payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    ingest_document(db, doc)
    return doc


@router.put("/documents/{slug}", response_model=KnowledgeDocumentOut)
def update_document(
    slug: str,
    payload: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    for field, value in payload.model_dump().items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    ingest_document(db, doc)  # re-chunk + re-embed since content may have changed
    return doc


@router.delete("/documents/{slug}", status_code=204)
def delete_document(
    slug: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    db.delete(doc)
    db.commit()


@router.post("/documents/{slug}/reindex", response_model=KnowledgeDocumentOut)
def reindex_document(
    slug: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Re-embeds a document's chunks under the currently active embedding
    model (e.g. after adding/removing VOYAGE_API_KEY) without editing content."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    ingest_document(db, doc)
    return doc


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge_base(payload: KnowledgeAskRequest, db: Session = Depends(get_db)):
    """
    General electrical Q&A grounded in the knowledge base (spec sections
    14-17, 41, 59). Distinct from /advisor/ask, which matches free text to
    a fixed, admin-authored troubleshooting record for safety-critical
    guidance - this endpoint answers open-ended "what is / how do I
    choose" questions, and always shows the sources it drew from.
    """
    results = search_knowledge(db, payload.query, top_k=4, category=payload.category)
    results = [r for r in results if r[2] >= RELEVANCE_FLOOR]

    if not results:
        return KnowledgeAskResponse(
            answer=None,
            answered_via=None,
            sources=[],
            message=(
                "I don't have enough verified information in the knowledge base "
                "to answer that yet. Try rephrasing, or ask the AI Electrical "
                "Advisor about a specific problem instead."
            ),
        )

    sources = [
        KnowledgeSourceOut(
            document_title=doc.title,
            document_slug=doc.slug,
            excerpt=chunk.content,
            relevance=round(score, 3),
        )
        for chunk, doc, score in results
    ]

    excerpts = [{"source": doc.title, "content": chunk.content} for chunk, doc, _ in results]
    answer = generate_grounded_answer(payload.query, excerpts)

    if answer:
        return KnowledgeAskResponse(answer=answer, answered_via="ai", sources=sources)

    # No AI configured, or the call failed - still genuinely useful: show
    # the raw, cited excerpts rather than nothing (spec section 59: be
    # transparent about what's available rather than silently failing).
    return KnowledgeAskResponse(
        answer=None,
        answered_via="excerpts",
        sources=sources,
        message="Here's what the knowledge base has on this topic:",
    )
