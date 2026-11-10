from datetime import date

from pydantic import BaseModel, Field


class DailyGoalUpdate(BaseModel):
    target_xp: int = Field(ge=10, le=200)


class DailyGoalStatus(BaseModel):
    day: date
    target_xp: int
    earned_xp: int
    remaining_xp: int
    completed: bool
