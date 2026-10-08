import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ServiceType(str, enum.Enum):
    find_electrician = "find_electrician"
    consultation = "consultation"
    installation = "installation"
    inspection = "inspection"
    estimate = "estimate"


class ServiceStatus(str, enum.Enum):
    submitted = "submitted"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    preferred_date = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.submitted)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="service_requests")
