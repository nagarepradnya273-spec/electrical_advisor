"""
Tests for the AI-assisted advisor matching, with the actual Anthropic call
mocked out (no API key or network access needed to run these).
"""
from unittest.mock import patch, MagicMock

from app.services import ai_service
from app.services.advisor_service import match_problem
from app.database import SessionLocal

PROBLEMS = [
    {"slug": "fan-running-slowly", "title": "Fan running slowly", "keywords": "fan,slow"},
    {"slug": "mcb-keeps-tripping", "title": "MCB keeps tripping", "keywords": "mcb,trip"},
]


def test_ai_unavailable_without_api_key():
    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", ""):
        assert ai_service.ai_available() is False
        assert ai_service.ai_match_problem_slug("my fan is slow", PROBLEMS) is None


def test_ai_returns_matched_slug():
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": [{"text": "fan-running-slowly"}]}
    mock_response.raise_for_status.return_value = None

    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.ai_service.httpx.post", return_value=mock_response) as mock_post:
            result = ai_service.ai_match_problem_slug("my ceiling fan barely spins", PROBLEMS)
            assert result == "fan-running-slowly"
            assert mock_post.call_count == 1


def test_ai_ignores_hallucinated_slug_not_in_list():
    """If the model returns something outside the known list, we must not trust it."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": [{"text": "some-made-up-slug"}]}
    mock_response.raise_for_status.return_value = None

    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.ai_service.httpx.post", return_value=mock_response):
            result = ai_service.ai_match_problem_slug("something unrelated", PROBLEMS)
            assert result is None


def test_ai_returns_none_when_response_is_none():
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": [{"text": "none"}]}
    mock_response.raise_for_status.return_value = None

    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.ai_service.httpx.post", return_value=mock_response):
            assert ai_service.ai_match_problem_slug("my cat knocked over a lamp", PROBLEMS) is None


def test_ai_falls_back_gracefully_on_network_error():
    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.ai_service.httpx.post", side_effect=Exception("network down")):
            assert ai_service.ai_match_problem_slug("my fan is slow", PROBLEMS) is None


def test_match_problem_uses_ai_when_available_and_reports_source():
    """End-to-end through advisor_service.match_problem against the seeded DB."""
    db = SessionLocal()
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": [{"text": "fan-running-slowly"}]}
    mock_response.raise_for_status.return_value = None

    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", "fake-key-for-test"):
        with patch("app.services.ai_service.httpx.post", return_value=mock_response):
            problem, matched_via = match_problem(db, "fan barely turning", "home")
            assert problem is not None
            assert problem.slug == "fan-running-slowly"
            assert matched_via == "ai"
    db.close()


def test_match_problem_falls_back_to_keyword_when_no_api_key():
    db = SessionLocal()
    with patch.object(ai_service.settings, "ANTHROPIC_API_KEY", ""):
        problem, matched_via = match_problem(db, "my fan is running slowly", "any")
        assert problem is not None
        assert problem.slug == "fan-running-slowly"
        assert matched_via == "keyword"
    db.close()
