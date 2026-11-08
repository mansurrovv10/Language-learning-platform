import uuid
from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Integer, DateTime, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.base import Base


class XPHistory(Base):
    __tablename__ = "xp_history"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    xp: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=datetime.utcnow)


class Streak(Base):
    __tablename__ = "streak"
    __table_args__ = (UniqueConstraint("user_id",name="uq_streak_user"),)

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    current_streak: Mapped[int] = mapped_column(Integer,default=0)
    last_activity: Mapped[date | None] = mapped_column(Date,nullable=True)


class Hearts(Base):
    __tablename__ = "hearts"
    __table_args__ = (UniqueConstraint("user_id",name="uq_hearts_user"),)

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    hearts: Mapped[int] = mapped_column(Integer,default=5)
    last_heart_lost_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)
