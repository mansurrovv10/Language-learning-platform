from datetime import date
from pydantic import BaseModel,ConfigDict


class ChallengeCreate(BaseModel):
    title: str
    description: str
    xp_reward: int = 0
    challenge_date: date


class ChallengeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    xp_reward: int | None = None
    challenge_date: date | None = None


class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    xp_reward: int
    challenge_date: date

    model_config = ConfigDict(from_attributes=True)