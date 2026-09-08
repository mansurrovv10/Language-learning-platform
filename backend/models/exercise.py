from enum import Enum as PyEnum

from sqlalchemy import Text, ForeignKey, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class ExerciseType(str, PyEnum):
    CHOICE = "choice"
    TRANSLATE = "translate"
    FILL_GAP = "fill_gap"
    MATCH = "match"


class Exercise(Base):
    __tablename__ = "exercise"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    lesson_id: Mapped[int] = mapped_column(Integer,ForeignKey("lesson.id"))
    type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[dict] = mapped_column(JSON)
    correct_answer: Mapped[dict] = mapped_column(JSON)