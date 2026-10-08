from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.product import CategoryOut


class AdvisorProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    place_context: str
    explanation: Optional[str] = None
    common_causes: Optional[str] = None
    safe_checks: Optional[str] = None
    when_to_call_electrician: Optional[str] = None
    danger_level: str


class AdvisorAskRequest(BaseModel):
    query: str
    place_context: Optional[str] = "any"


class AdvisorAskResponse(BaseModel):
    matched: bool
    matched_via: Optional[str] = None  # "ai" or "keyword" - which matcher found this
    problem: Optional[AdvisorProblemOut] = None
    recommended_categories: List[CategoryOut] = []
    message: str
