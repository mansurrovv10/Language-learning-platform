from datetime import datetime

from pydantic import BaseModel

from backend.models.exercise import ExerciseType


class DueReviewItem(BaseModel):
    exercise_id: int
    exercise_type: ExerciseType
    question: str
    options: dict
    box: int
    due_at: datetime
    last_result: bool | None
    attempts: int
