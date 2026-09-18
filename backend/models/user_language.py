import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.models.course import LevelChoices


class UserLanguage(Base):
    __tablename__ = "user_language"

    __table_args__ = (UniqueConstraint("user_id", "language_id", name="uq_user_language_user_language"),)

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    language_id: Mapped[int] = mapped_column(Integer,ForeignKey("language.id"))
    level: Mapped[LevelChoices|None] = mapped_column(Enum(LevelChoices),nullable=True)
    placement_completed: Mapped[bool] = mapped_column(Boolean,default=False)
