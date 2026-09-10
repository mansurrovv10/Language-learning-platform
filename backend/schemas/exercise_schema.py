from pydantic import BaseModel
from backend.models.exercise import ExerciseType


class ExerciseCreate(BaseModel):
    lesson_id: int
    type: ExerciseType
    question: str
    options: dict
    correct_answer: dict


class ExerciseUpdate(BaseModel):
    lesson_id: int
    type: ExerciseType
    question: str
    options: dict
    correct_answer: dict


class ExerciseResponse(BaseModel):
    id: int
    lesson_id: int
    type: ExerciseType
    question: str
    options: dict
    correct_answer: dict

    class Config:
        from_attributes = True

class ExerciseResult(BaseModel):
    correct: bool
    score: int