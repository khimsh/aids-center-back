from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DoctorCreate(BaseModel):
    name: str
    picture: Optional[str] = None
    education: str
    experience: str


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None


class DoctorOut(BaseModel):
    id: int
    name: str
    picture: Optional[str]
    education: str
    experience: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
