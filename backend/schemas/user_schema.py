from typing import Optional
from pydantic import BaseModel, EmailStr
from backend.models.user import UserRole

class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class RoleUpdateSchema(BaseModel):
    role: UserRole


class ActiveUpdateSchema(BaseModel):
    is_active: bool