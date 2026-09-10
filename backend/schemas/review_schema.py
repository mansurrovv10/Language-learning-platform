import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReviewCreate(BaseModel):
    user_id: uuid.UUID
    course_id: int
    rating: int
    comment: str


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    course_id: int
    rating: int
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)