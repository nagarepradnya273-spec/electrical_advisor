import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class DangerLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AdvisorProblem(Base):
    """
    One entry in the 'Shop by Problem' / Electrical Advisor decision tree
    (spec sections 8-10). This is the core USP: turning a plain-language
    problem into safe guidance + relevant product categories.
    """
    __tablename__ = "advisor_problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)  # e.g. "Fan running slowly"
    slug = Column(String(200), unique=True, index=True, nullable=False)
    keywords = Column(String(500), nullable=False)  # comma-separated, for v1 keyword matching
    place_context = Column(String(50), default="any")  # home / office / shop / hospital / any

    explanation = Column(Text, nullable=True)
    common_causes = Column(Text, nullable=True)
    safe_checks = Column(Text, nullable=True)
    when_to_call_electrician = Column(Text, nullable=True)
    danger_level = Column(Enum(DangerLevel), default=DangerLevel.low)

    recommendations = relationship(
        "AdvisorProductRecommendation", back_populates="problem", cascade="all, delete-orphan"
    )


class AdvisorProductRecommendation(Base):
    """
    Links a problem to relevant product CATEGORIES (not specific SKUs), so
    recommendations always resolve against the live catalogue rather than
    hard-coded product references (spec section 30: don't invent specs).
    """
    __tablename__ = "advisor_product_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("advisor_problems.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    problem = relationship("AdvisorProblem", back_populates="recommendations")
    category = relationship("Category")
