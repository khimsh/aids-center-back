from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobPostingCreate(BaseModel):
    title_ka:       str
    title_en:       Optional[str] = None
    description_ka: Optional[str] = None
    description_en: Optional[str] = None
    department_ka:  Optional[str] = None
    department_en:  Optional[str] = None
    deadline:       Optional[datetime] = None
    published:      bool = False
    published_at:   Optional[datetime] = None


class JobPostingUpdate(BaseModel):
    title_ka:       Optional[str] = None
    title_en:       Optional[str] = None
    description_ka: Optional[str] = None
    description_en: Optional[str] = None
    department_ka:  Optional[str] = None
    department_en:  Optional[str] = None
    deadline:       Optional[datetime] = None
    published:      Optional[bool] = None
    published_at:   Optional[datetime] = None


class JobPostingOut(BaseModel):
    id:             int
    title_ka:       str
    title_en:       Optional[str]
    description_ka: Optional[str]
    description_en: Optional[str]
    department_ka:  Optional[str]
    department_en:  Optional[str]
    deadline:       Optional[datetime]
    published:      bool
    published_at:   Optional[datetime]
    created_at:     datetime
    updated_at:     datetime

    model_config = {"from_attributes": True}
