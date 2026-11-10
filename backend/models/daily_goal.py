import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.time import utc_now


class UserDailyGoal(Base):
    __tablename__ = "user_daily_goal"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_daily_goal_user"),
        CheckConstraint(
            "target_xp >= 10 AND target_xp <= 200",
            name="ck_user_daily_goal_target",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    target_xp: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
