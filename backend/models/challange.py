from datetime import date

from sqlalchemy import String, Text, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class DailyChallenge(Base):
    __tablename__ = "daily_challenge"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    xp_reward: Mapped[int] = mapped_column(Integer,default=0)
    challenge_date: Mapped[date] = mapped_column(Date,unique=True)