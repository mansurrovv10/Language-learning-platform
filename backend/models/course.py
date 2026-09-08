from enum import Enum as PyEnum

from sqlalchemy import String, Text, ForeignKey, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class LevelChoices(str, PyEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    language_id: Mapped[int] = mapped_column(Integer,ForeignKey("language.id"))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    level: Mapped[LevelChoices] = mapped_column(Enum(LevelChoices),default=LevelChoices.A1)
    order: Mapped[int] = mapped_column(Integer)