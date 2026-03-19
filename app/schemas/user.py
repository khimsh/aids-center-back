from pydantic import BaseModel, EmailStr
from datetime import datetime


class LoginRequest(BaseModel):
    username: str  # treated as email, matches frontend contract
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "editor"  # admin | editor


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    new_password: str
