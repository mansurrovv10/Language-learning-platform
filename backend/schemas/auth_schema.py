from uuid import UUID
from datetime import datetime
from backend.models.user import UserRole
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class RegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3,max_length=50)
    password: str = Field(min_length=8,max_length=100)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshSchema(BaseModel):
    refresh_token: str


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime


class RefreshTokenResponseSchema(BaseModel):
    id: int
    token: str
    created_date: datetime



