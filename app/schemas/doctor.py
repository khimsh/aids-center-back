from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DoctorCreate(BaseModel):
    name: str
    picture: Optional[str] = None
    profile_url: Optional[str] = None
    specialty: Optional[str] = None
    degree: Optional[str] = None
    department: Optional[str] = None
    education: str
    experience: str
    pedagogical_experience: Optional[str] = None
    memberships: Optional[str] = None
    publications: Optional[str] = None
    expertise: Optional[str] = None
    sort_order: Optional[int] = None


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None
    profile_url: Optional[str] = None
    specialty: Optional[str] = None
    degree: Optional[str] = None
    department: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    pedagogical_experience: Optional[str] = None
    memberships: Optional[str] = None
    publications: Optional[str] = None
    expertise: Optional[str] = None
    sort_order: Optional[int] = None


class DoctorReorderItem(BaseModel):
    id: int
    sort_order: int


class DoctorReorderRequest(BaseModel):
    items: list[DoctorReorderItem]


class DoctorReorderByIdsRequest(BaseModel):
    ids: list[int]


class DoctorMoveRequest(BaseModel):
    ids: list[int]
    before_id: Optional[int] = None
    after_id: Optional[int] = None


class DoctorTranslationBase(BaseModel):
    lang: str
    name: str
    specialty: Optional[str] = None
    degree: Optional[str] = None
    department: Optional[str] = None
    education: str
    experience: str
    pedagogical_experience: Optional[str] = None
    memberships: Optional[str] = None
    publications: Optional[str] = None
    expertise: Optional[str] = None


class DoctorTranslationCreate(DoctorTranslationBase):
    pass


class DoctorTranslationUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    degree: Optional[str] = None
    department: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    pedagogical_experience: Optional[str] = None
    memberships: Optional[str] = None
    publications: Optional[str] = None
    expertise: Optional[str] = None


class DoctorTranslationOut(DoctorTranslationBase):
    id: int
    doctor_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DoctorOut(BaseModel):
    id: int
    name: str
    picture: Optional[str]
    profile_url: Optional[str]
    specialty: Optional[str]
    degree: Optional[str]
    department: Optional[str]
    education: str
    experience: str
    pedagogical_experience: Optional[str]
    memberships: Optional[str]
    publications: Optional[str]
    expertise: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
