from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import ServiceRequest
from app.models.user import User
from app.schemas.service import ServiceRequestOut, ServiceRequestCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/", response_model=ServiceRequestOut, status_code=201)
def create_service_request(
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = ServiceRequest(user_id=current_user.id, **payload.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/", response_model=List[ServiceRequestOut])
def list_my_service_requests(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(ServiceRequest).filter(ServiceRequest.user_id == current_user.id).all()
