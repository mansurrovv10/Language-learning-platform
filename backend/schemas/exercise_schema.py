from typing import Any, Optional

from pydantic import BaseModel

from backend.models.exercise import ExerciseType


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

    class Config:
        from_attributes = True


class ExerciseSubmit(BaseModel):
    answer: Any


class ExerciseResult(BaseModel):
    correct: bool
    score: int