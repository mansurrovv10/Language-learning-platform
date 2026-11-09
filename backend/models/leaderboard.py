import uuid
from datetime import datetime
from sqlalchemy import ForeignKey,Integer,DateTime,Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import Base


class Leaderboard(Base):
    __tablename__ = "leaderboard"
    __table_args__ = (
        Index("ix_leaderboard_user_id","user_id",unique=True),
    )

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    xp: Mapped[int] = mapped_column(Integer,default=0)
    rank: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserProfile"] = relationship(lazy="joined")
