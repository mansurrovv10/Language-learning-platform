from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class Lesson(Base):
    __tablename__ = "lesson"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    course_id: Mapped[int] = mapped_column(Integer,ForeignKey("course.id"))
    title: Mapped[str] = mapped_column(String)
    order: Mapped[int] = mapped_column(Integer)
    is_locked: Mapped[bool] = mapped_column(Boolean,default=False)