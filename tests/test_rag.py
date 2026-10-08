"""
Tests for the RAG knowledge base: chunking, the dependency-free fallback
embedding, ingestion + retrieval against the real (seeded) database, and
the /knowledge/ask endpoint with the Anthropic call mocked out - same
approach as test_ai_advisor.py, so none of this needs network access or
an API key to run.
"""
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.knowledge import KnowledgeDocument
from app.services import embedding_service
from app.services.rag_service import chunk_text, ingest_document, search_knowledge
from app.services import knowledge_ai_service

client = TestClient(app)


# --- Chunking -----------------------------------------------------------

def test_chunk_text_keeps_short_paragraphs_together():
    text = "First short paragraph.\n\nSecond short paragraph."
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) == 1
    assert "First short paragraph." in chunks[0]
    assert "Second short paragraph." in chunks[0]


def test_chunk_text_splits_when_exceeding_chunk_size():
    para_a = "A" * 100
    para_b = "B" * 100
    text = f"{para_a}\n\n{para_b}"
    chunks = chunk_text(text, chunk_size=120, overlap=10)
    assert len(chunks) == 2
    assert chunks[0].strip() == para_a
    assert chunks[1].strip() == para_b


def test_chunk_text_hard_wraps_a_single_oversized_paragraph():
    huge_para = "word " * 400  # single paragraph, no blank lines
    chunks = chunk_text(huge_para, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


# --- Fallback embedding ---------------------------------------------------

def test_fallback_embedding_is_deterministic():
    v1 = embedding_service._fallback_embedding("MCB tripping circuit breaker")
    v2 = embedding_service._fallback_embedding("MCB tripping circuit breaker")
    assert v1 == v2


def test_fallback_embedding_is_unit_normalised():
    vector = embedding_service._fallback_embedding("some sample electrical text here")
    norm = sum(v * v for v in vector.values()) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_cosine_similarity_identical_vectors_is_one():
    vector = embedding_service._fallback_embedding("residual current device earth leakage")
    assert abs(embedding_service.cosine_similarity(vector, vector) - 1.0) < 1e-9


def test_cosine_similarity_unrelated_text_is_zero():
    """With sparse (non-hashed) vectors, text sharing no vocabulary at all
    has exactly zero overlap - no collision noise to guard against."""
    a = embedding_service._fallback_embedding("miniature circuit breaker overload protection")
    b = embedding_service._fallback_embedding("chocolate cake baking recipe oven")
    assert embedding_service.cosine_similarity(a, b) == 0.0


def test_get_embedding_falls_back_without_voyage_key():
    with patch.object(embedding_service.settings, "VOYAGE_API_KEY", ""):
        assert embedding_service.embedding_model_name() == embedding_service.FALLBACK_MODEL_NAME
        vector = embedding_service.get_embedding("MCB basics")
        assert isinstance(vector, dict)
        assert len(vector) > 0


# --- Ingestion + retrieval, against a real (throwaway) document ----------

def test_ingest_and_search_finds_relevant_chunk():
    db = SessionLocal()
    doc = KnowledgeDocument(
        title="Test Doc: Ceiling Fan Capacitors",
        slug="test-doc-fan-capacitors",
        category="fans",
        content=(
            "A capacitor helps a ceiling fan motor start and run at full speed.\n\n"
            "A weak capacitor is a common cause of a fan running slowly."
        ),
        is_demo=True,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        with patch.object(embedding_service.settings, "VOYAGE_API_KEY", ""):
            chunk_count = ingest_document(db, doc)
            assert chunk_count >= 1

            results = search_knowledge(db, "why does my ceiling fan run slowly", top_k=3)
            matched_slugs = {d.slug for _, d, _ in results}
            assert "test-doc-fan-capacitors" in matched_slugs

            top_chunk, top_doc, top_score = results[0]
            assert top_score > 0
    finally:
        db.delete(doc)
        db.commit()
        db.close()


def test_search_knowledge_returns_seeded_mcb_content():
    """Relies on conftest.py having already run seed_data.py (which seeds
    the knowledge base too) against the shared test database."""
    db = SessionLocal()
    try:
        with patch.object(embedding_service.settings, "VOYAGE_API_KEY", ""):
            results = search_knowledge(db, "what does an MCB protect against", top_k=3)
            assert len(results) > 0
            assert any(d.slug == "mcb-basics" for _, d, _ in results)
    finally:
        db.close()


# --- Grounded generation (Claude call mocked, same pattern as ai_service) -

def test_generate_grounded_answer_without_api_key_returns_none():
    with patch.object(knowledge_ai_service.settings, "ANTHROPIC_API_KEY", ""):
        result = knowledge_ai_service.generate_grounded_answer(
            "What is an MCB?", [{"source": "MCB Basics", "content": "An MCB is a circuit breaker."}]
        )
        assert result is None


def test_generate_grounded_answer_uses_excerpts():
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": [{"text": "An MCB automatically switches off a circuit on overload."}]}
    mock_response.raise_for_status.return_value = None

    with patch.object(knowledge_ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.knowledge_ai_service.httpx.post", return_value=mock_response) as mock_post:
            result = knowledge_ai_service.generate_grounded_answer(
                "What is an MCB?", [{"source": "MCB Basics", "content": "An MCB is a circuit breaker."}]
            )
            assert "MCB" in result
            assert mock_post.call_count == 1


def test_generate_grounded_answer_falls_back_gracefully_on_error():
    with patch.object(knowledge_ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.knowledge_ai_service.httpx.post", side_effect=Exception("network down")):
            result = knowledge_ai_service.generate_grounded_answer(
                "What is an MCB?", [{"source": "MCB Basics", "content": "An MCB is a circuit breaker."}]
            )
            assert result is None


# --- /knowledge/ask endpoint ----------------------------------------------

def test_knowledge_ask_without_api_key_returns_cited_excerpts():
    with patch.object(knowledge_ai_service.settings, "ANTHROPIC_API_KEY", ""):
        r = client.post("/knowledge/ask", json={"query": "what is the difference between RCCB and MCB"})
        assert r.status_code == 200
        body = r.json()
        assert body["answered_via"] == "excerpts"
        assert body["answer"] is None
        assert len(body["sources"]) > 0
        assert any("rccb" in s["document_slug"] for s in body["sources"])


def test_knowledge_ask_uses_ai_when_available():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"text": "An RCCB protects people from shock; an MCB protects wiring from overload."}]
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(knowledge_ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.knowledge_ai_service.httpx.post", return_value=mock_response):
            r = client.post("/knowledge/ask", json={"query": "what is the difference between RCCB and MCB"})
            assert r.status_code == 200
            body = r.json()
            assert body["answered_via"] == "ai"
            assert "RCCB" in body["answer"]
            assert len(body["sources"]) > 0


def test_knowledge_ask_returns_no_match_message_for_unrelated_query():
    r = client.post("/knowledge/ask", json={"query": "how do I bake a chocolate cake"})
    assert r.status_code == 200
    body = r.json()
    assert body["answered_via"] is None
    assert body["sources"] == []
    assert body["message"]


def test_knowledge_documents_list_is_public():
    r = client.get("/knowledge/documents")
    assert r.status_code == 200
    slugs = {d["slug"] for d in r.json()}
    assert "mcb-basics" in slugs
    assert "electrical-safety-basics" in slugs


def test_knowledge_document_create_requires_admin():
    r = client.post(
        "/knowledge/documents",
        json={"title": "x", "slug": "unauthorized-test-doc", "category": "safety", "content": "x"},
    )
    assert r.status_code == 401  # no auth token at all
