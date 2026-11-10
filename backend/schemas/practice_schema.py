import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.models.exercise import ExerciseType
from backend.schemas.gamification_schema import HeartsResponse


class PracticeItemResponse(BaseModel):
    id: int
    exercise_id: int
    position: int
    exercise_type: ExerciseType
    question: str
    options: dict


class PracticeSessionResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    items: list[PracticeItemResponse]


class PracticeAnswer(BaseModel):
    item_id: int
    answer: Any


class PracticeCompletion(BaseModel):
    answers: list[PracticeAnswer] = Field(min_length=1, max_length=3)


class PracticeResult(BaseModel):
    session_id: uuid.UUID
    score: float
    passed: bool
    heart_awarded: bool
    hearts_left: int
    heart_status: HeartsResponse
