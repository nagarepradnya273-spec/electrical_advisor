from sqlalchemy.orm import Session

from app.models.advisor import AdvisorProblem
from app.services.ai_service import ai_available, ai_match_problem_slug


def _keyword_match(problems: list[AdvisorProblem], query: str) -> AdvisorProblem | None:
    """Transparent, admin-editable keyword matching - always available, no API key needed."""
    query_lower = query.lower()
    best_match = None
    best_score = 0

    for problem in problems:
        keywords = [k.strip().lower() for k in problem.keywords.split(",") if k.strip()]
        score = sum(1 for kw in keywords if kw in query_lower)
        if problem.title.lower() in query_lower:
            score += 2
        if score > best_score:
            best_score = score
            best_match = problem

    return best_match if best_score > 0 else None


def match_problem(db: Session, query: str, place_context: str = "any") -> tuple[AdvisorProblem | None, str | None]:
    """
    Tries Claude first (if ANTHROPIC_API_KEY is configured) for a smarter,
    more forgiving match, then falls back to keyword matching - both for
    reliability, and so this endpoint works with zero setup out of the box.

    Returns (matched_problem_or_None, "ai" | "keyword" | None).
    """
    problems = db.query(AdvisorProblem).all()
    if not problems:
        return None, None

    if ai_available():
        problem_dicts = [{"slug": p.slug, "title": p.title, "keywords": p.keywords} for p in problems]
        slug = ai_match_problem_slug(query, problem_dicts, place_context)
        if slug:
            match = next((p for p in problems if p.slug == slug), None)
            if match:
                return match, "ai"

    match = _keyword_match(problems, query)
    return match, ("keyword" if match else None)
