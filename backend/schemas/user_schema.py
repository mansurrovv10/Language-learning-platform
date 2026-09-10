from typing import Optional
from pydantic import BaseModel, EmailStr

class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None