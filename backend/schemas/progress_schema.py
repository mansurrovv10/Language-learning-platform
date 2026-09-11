import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProgressUpdate(BaseModel):
    completed: bool | None = None
    score: int | None = None


class ProgressResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    lesson_id: int
    completed: bool
    score: int
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)