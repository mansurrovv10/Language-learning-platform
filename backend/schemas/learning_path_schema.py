from pydantic import BaseModel, ConfigDict

from backend.models.course import LevelChoices
from backend.schemas.lessons_schema import LessonResponse


class LearningCourseResponse(BaseModel):
    id: int
    language_id: int
    title: str
    description: str
    level: LevelChoices
    order: int
    is_unlocked: bool
    lessons: list[LessonResponse]

    model_config = ConfigDict(from_attributes=True)


class LearningPathResponse(BaseModel):
    language_id: int
    level: LevelChoices | None
    placement_completed: bool
    courses: list[LearningCourseResponse]
