import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class UserExerciseProgress(Base):
    __tablename__ = "user_exercise_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_progress_user_exercise"),)

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    exercise_id: Mapped[int] = mapped_column(Integer,ForeignKey("exercise.id"))
    completed: Mapped[bool] = mapped_column(Boolean,default=False)
    score: Mapped[int] = mapped_column(Integer,default=0)
