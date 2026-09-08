import uuid
from datetime import datetime

from enum import Enum as PyEnum

from sqlalchemy import ForeignKey, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class ChatType(str, PyEnum):
    PRIVATE = "private"
    GROUP = "group"


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType))
    language_id: Mapped[int] = mapped_column(Integer,ForeignKey("language.id"),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ChatMember(Base):
    __tablename__ = "chat_member"

    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("chat.id"),primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"),primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime)