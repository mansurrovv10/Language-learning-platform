from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,ConfigDict


class AchievementCreate(BaseModel):
    title: str
    description: str
    xp_reward: int = 0
    conditions: dict | None = None


class AchievementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    xp_reward: int | None = None
    conditions: dict | None = None


class AchievementResponse(BaseModel):
    id: int
    title: str
    description: str
    xp_reward: int
    conditions: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class UserAchievementResponse(BaseModel):
    id: int
    user_id: UUID
    achievement_id: int
    earned_at: datetime

    model_config = ConfigDict(from_attributes=True)