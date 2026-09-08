import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class MessageReaction(Base):
    __tablename__ = "message_reaction"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("message.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    reaction: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)