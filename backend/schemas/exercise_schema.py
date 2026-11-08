from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from backend.models.exercise import ExerciseType
from backend.schemas.gamification_schema import HeartsResponse


class ExerciseCreate(BaseModel):
    lesson_id: int
    type: ExerciseType
    question: str
    options: dict
    correct_answer: Any


class ExerciseUpdate(BaseModel):
    lesson_id: Optional[int] = None
    type: Optional[ExerciseType] = None
    question: Optional[str] = None
    options: Optional[dict] = None
    correct_answer: Optional[Any] = None


class ExerciseResponse(BaseModel):
    id: int
    lesson_id: int
    type: ExerciseType
    question: str
    options: dict

    model_config = ConfigDict(from_attributes=True)


class ExerciseSubmit(BaseModel):
    answer: Any


class ExerciseResult(BaseModel):
    correct: bool
    score: int
    hearts_left: int
    heart_status: HeartsResponse | None = None
