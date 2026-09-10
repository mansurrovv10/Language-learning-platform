import uuid
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class XPCreate(BaseModel):
    user_id: uuid.UUID
    xp: int
    reason: str


class XPResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    xp: int
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StreakResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    current_streak: int
    last_activity: date | None

    model_config = ConfigDict(from_attributes=True)