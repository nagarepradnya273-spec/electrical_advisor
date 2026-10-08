from typing import Optional

from pydantic import BaseModel, ConfigDict


class ServiceRequestCreate(BaseModel):
    service_type: str
    description: str
    location: Optional[str] = None
    preferred_date: Optional[str] = None
    photo_url: Optional[str] = None


class ServiceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_type: str
    description: str
    location: Optional[str] = None
    status: str
