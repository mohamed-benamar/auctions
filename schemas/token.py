from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    role: str

# Schéma personnalisé sans email mais avec le nom complet
class TokenCustomResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str
    user_full_name: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
