import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text,ForeignKey,DateTime,Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column,relationship
from backend.database.base import Base
from backend.time import utc_now

if TYPE_CHECKING:
    from backend.models.user import UserProfile


class Message(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("chat.id"),nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("user.id"),nullable=False)
    content: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utc_now)
    is_read: Mapped[bool] = mapped_column(Boolean,default=False)

    sender: Mapped["UserProfile"] = relationship(lazy="joined")
