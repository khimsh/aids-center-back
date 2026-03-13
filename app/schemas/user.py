from pydantic import BaseModel


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
