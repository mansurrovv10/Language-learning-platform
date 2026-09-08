import uuid
from datetime import datetime, date

from sqlalchemy import String, ForeignKey, Integer, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class XPHistory(Base):
    __tablename__ = "xp_history"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    xp: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Streak(Base):
    __tablename__ = "streak"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    current_streak: Mapped[int] = mapped_column(Integer,default=0)
    last_activity: Mapped[date] = mapped_column(Date)