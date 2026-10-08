from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeDocument(Base):
    """
    A source document for the RAG knowledge base (spec sections 14, 46) -
    buying guides, safety explainers, product-category basics, etc.

    Kept deliberately separate from AdvisorProblem: AdvisorProblem drives
    the narrow, safety-critical troubleshooting flow (admin-authored,
    closed-set matching only - see advisor_service.py). KnowledgeDocument
    feeds the open-ended "ask a question" RAG flow, where Claude may
    generate an answer, but ONLY grounded in retrieved chunks from here,
    with citations (see knowledge_ai_service.py).
    """
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=False)  # e.g. protection, wiring, safety, buying_guide
    content = Column(Text, nullable=False)  # full source text; chunked + embedded on ingest
    is_demo = Column(Boolean, default=True)  # spec section 46: label seeded/demo knowledge content
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    # Embedding stored as a JSON-encoded list of floats. This keeps the
    # same column working on SQLite (dev default) and PostgreSQL (prod)
    # without requiring the pgvector extension to be installed. For a
    # knowledge base this size (tens-hundreds of chunks), cosine similarity
    # is computed in Python at query time (see rag_service.search_knowledge).
    # If the catalogue grows into the thousands, swap this for a pgvector
    # Vector column and use `<=>` in SQL instead - nothing else in the RAG
    # module needs to change, since callers only see (chunk, document, score).
    embedding = Column(Text, nullable=False)
    embedding_model = Column(String(50), nullable=False)  # which embedder produced it

    document = relationship("KnowledgeDocument", back_populates="chunks")
