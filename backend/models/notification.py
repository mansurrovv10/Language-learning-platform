import uuid
from datetime import datetime

from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, Integer, DateTime, Enum,Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class NotificationType(str, PyEnum):
    FRIEND_REQUEST = "friend_request"
    ACHIEVEMENT = "achievement"
    MESSAGE = "message"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    title: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    is_read: Mapped[bool] = mapped_column(Boolean,default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)