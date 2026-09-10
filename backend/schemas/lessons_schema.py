from pydantic import BaseModel, ConfigDict


class LessonCreate(BaseModel):
    course_id: int
    title: str
    order: int
    is_locked: bool = False


class LessonUpdate(BaseModel):
    course_id: int
    title: str
    order: int
    is_locked: bool


class LessonResponse(BaseModel):
    id: int
    course_id: int
    title: str
    order: int
    is_locked: bool

    model_config = ConfigDict(from_attributes=True)