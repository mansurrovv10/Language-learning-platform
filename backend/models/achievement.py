import uuid
from datetime import datetime

from sqlalchemy import String,Text,ForeignKey,Integer,DateTime,UniqueConstraint,JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column

from backend.database.base import Base


class Achievement(Base):
    __tablename__ = "achievement"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    xp_reward: Mapped[int] = mapped_column(Integer,default=0)
    conditions: Mapped[dict | None] = mapped_column(JSON,nullable=True)
    conditions: Mapped[dict | None] = mapped_column(JSON,nullable=True)


class UserAchievement(Base):
    __tablename__ = "user_achievement"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "achievement_id",
            name="uq_user_achievement_user_achievement"
        ),
    )

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id")
    )
    achievement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("achievement.id")
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )