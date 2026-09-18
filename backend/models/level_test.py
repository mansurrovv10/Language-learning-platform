import uuid
from datetime import datetime
from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text, JSON, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.base import Base
from backend.models.course import LevelChoices
from backend.models.exercise import ExerciseType


class LevelTest(Base):
    __tablename__ = "level_test"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    language_id: Mapped[int] = mapped_column(Integer,ForeignKey("language.id"))
    is_placement: Mapped[bool] = mapped_column(default=True)
    target_level: Mapped[LevelChoices|None] = mapped_column(Enum(LevelChoices),nullable=True)
    passing_score: Mapped[int] = mapped_column(Integer,default=70)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)


class LevelTestQuestion(Base):
    __tablename__ = "level_test_question"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    test_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("level_test.id"))
    level: Mapped[LevelChoices] = mapped_column(Enum(LevelChoices))
    type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[dict] = mapped_column(JSON)
    correct_answer: Mapped[dict] = mapped_column(JSON)
    order: Mapped[int] = mapped_column(Integer,default=1)


class LevelTestAttempt(Base):
    __tablename__ = "level_test_attempt"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    test_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("level_test.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    language_id: Mapped[int] = mapped_column(Integer,ForeignKey("language.id"))
    score: Mapped[float|None] = mapped_column(Float,nullable=True)
    result_level: Mapped[LevelChoices|None] = mapped_column(Enum(LevelChoices),nullable=True)
    passed: Mapped[bool|None] = mapped_column(Boolean,nullable=True)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
