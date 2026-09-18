from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.models.course import LevelChoices
from backend.models.exercise import ExerciseType


class LevelTestCreate(BaseModel):
    language_id: int
    is_placement: bool
    target_level: LevelChoices | None = None
    passing_score: int = Field(default=70,ge=1,le=100)
    is_active: bool = True


class LevelTestUpdate(BaseModel):
    target_level: LevelChoices | None = None
    passing_score: int | None = Field(default=None,ge=1,le=100)
    is_active: bool | None = None


class LevelTestResponse(BaseModel):
    id: UUID
    language_id: int
    is_placement: bool
    target_level: LevelChoices | None
    passing_score: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LevelTestQuestionCreate(BaseModel):
    level: LevelChoices
    type: ExerciseType
    question: str = Field(min_length=1)
    options: dict
    correct_answer: Any
    order: int = Field(default=1,ge=1)


class LevelTestQuestionUpdate(BaseModel):
    level: LevelChoices | None = None
    type: ExerciseType | None = None
    question: str | None = Field(default=None,min_length=1)
    options: dict | None = None
    correct_answer: Any | None = None
    order: int | None = Field(default=None,ge=1)


class LevelTestQuestionResponse(BaseModel):
    id: int
    test_id: UUID
    level: LevelChoices
    type: ExerciseType
    question: str
    options: dict
    order: int

    model_config = ConfigDict(from_attributes=True)


class LevelTestQuestionAdminResponse(LevelTestQuestionResponse):
    correct_answer: Any


class LevelTestStartResponse(BaseModel):
    attempt_id: UUID
    test_id: UUID
    is_placement: bool
    target_level: LevelChoices | None
    questions: list[LevelTestQuestionResponse]


class LevelTestAnswer(BaseModel):
    question_id: int
    answer: Any


class LevelTestSubmit(BaseModel):
    answers: list[LevelTestAnswer] = Field(min_length=1)


class LevelTestResultResponse(BaseModel):
    attempt_id: UUID
    score: float
    passed: bool
    result_level: LevelChoices | None
