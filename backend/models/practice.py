import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.time import utc_now


class PracticeSession(Base):
    __tablename__ = "practice_session"
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_practice_session_score",
        ),
        CheckConstraint(
            "expires_at > created_at", name="ck_practice_session_expiry"
        ),
        CheckConstraint(
            "completed_at IS NULL OR "
            "(score IS NOT NULL AND passed IS NOT NULL "
            "AND request_hash IS NOT NULL AND response IS NOT NULL)",
            name="ck_practice_session_completion",
        ),
        CheckConstraint(
            "NOT heart_awarded OR (completed_at IS NOT NULL AND passed)",
            name="ck_practice_session_heart_award",
        ),
        Index("ix_practice_session_user_created", "user_id", "created_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    heart_awarded: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    request_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PracticeSessionItem(Base):
    __tablename__ = "practice_session_item"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "position", name="uq_practice_item_session_position"
        ),
        UniqueConstraint(
            "session_id", "exercise_id", name="uq_practice_item_session_exercise"
        ),
        CheckConstraint("position >= 0", name="ck_practice_item_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_session.id"), nullable=False, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercise.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(32), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[dict] = mapped_column(JSON, nullable=False)
