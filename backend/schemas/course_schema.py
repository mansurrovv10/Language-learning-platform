from pydantic import BaseModel
from backend.models.course import LevelChoices


class CourseCreate(BaseModel):
    language_id: int
    title: str
    description: str
    level: LevelChoices
    order: int


class CourseUpdate(BaseModel):
    language_id: int
    title: str
    description: str
    level: LevelChoices
    order: int


class CourseResponse(BaseModel):
    id: int
    language_id: int
    title: str
    description: str
    level: LevelChoices
    order: int

    class Config:
        from_attributes = True