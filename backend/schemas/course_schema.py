from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.models.course import LevelChoices


class CourseCreate(BaseModel):
    language_id: int
    title: str
    description: str
    level: LevelChoices
    order: int


class CourseUpdate(BaseModel):
    language_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[LevelChoices] = None
    order: Optional[int] = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language_id: int
    title: str
    description: str
    level: LevelChoices
    order: int
