import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    lesson_id: Mapped[int] = mapped_column(Integer,ForeignKey("lesson.id"))
    completed: Mapped[bool] = mapped_column(Boolean,default=False)
    score: Mapped[int] = mapped_column(Integer,default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime,nullable=True)