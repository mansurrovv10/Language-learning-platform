import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProgressCreate(BaseModel):
    user_id: uuid.UUID
    lesson_id: int
    completed: bool = False
    score: int = 0


class ProgressUpdate(BaseModel):
    completed: Optional[bool] = None
    score: Optional[int] = None


class ProgressResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    lesson_id: int
    completed: bool
    score: int
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)