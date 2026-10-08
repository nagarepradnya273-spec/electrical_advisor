from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.advisor import AdvisorProblem
from app.schemas.advisor import AdvisorProblemOut, AdvisorAskRequest, AdvisorAskResponse
from app.services.advisor_service import match_problem

router = APIRouter(prefix="/advisor", tags=["Advisor"])


@router.get("/problems", response_model=List[AdvisorProblemOut])
def list_problems(db: Session = Depends(get_db)):
    return db.query(AdvisorProblem).all()


@router.get("/problems/{slug}", response_model=AdvisorProblemOut)
def get_problem(slug: str, db: Session = Depends(get_db)):
    problem = db.query(AdvisorProblem).filter(AdvisorProblem.slug == slug).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.post("/ask", response_model=AdvisorAskResponse)
def ask_advisor(payload: AdvisorAskRequest, db: Session = Depends(get_db)):
    """
    The core 'Describe your problem' endpoint (spec sections 2 and 8-9).
    v1 uses transparent keyword matching; an AI classifier can replace
    match_problem() later without changing this response shape.
    """
    problem, matched_via = match_problem(db, payload.query, payload.place_context)

    if not problem:
        return AdvisorAskResponse(
            matched=False,
            matched_via=None,
            problem=None,
            recommended_categories=[],
            message=(
                "We couldn't confidently match your problem. Try describing it "
                "differently, or ask an expert on WhatsApp / request a consultation."
            ),
        )

    categories = [rec.category for rec in problem.recommendations]
    message = f"Here's some guidance for: {problem.title}"
    if problem.danger_level.value == "high":
        message += (
            " \u26a0\ufe0f This may be unsafe to handle yourself — switch off power "
            "at the MCB and contact a qualified electrician."
        )

    return AdvisorAskResponse(
        matched=True,
        matched_via=matched_via,
        problem=problem,
        recommended_categories=categories,
        message=message,
    )
