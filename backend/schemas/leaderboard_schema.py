import uuid
from datetime import datetime

from pydantic import BaseModel,ConfigDict


class LeaderboardResponse(BaseModel):
    user_id: uuid.UUID
    xp: int
    rank: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLeaderboardResponse(BaseModel):
    user_id: uuid.UUID
    xp: int
    rank: int | None = None