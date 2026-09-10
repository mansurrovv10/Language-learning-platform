import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey,DateTime,Enum,Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column
from backend.database.base import Base

class FriendRequestStatus(str,PyEnum):
    PENDING="pending"
    ACCEPTED="accepted"
    REJECTED="rejected"

class FriendRequest(Base):
    __tablename__="friend_request"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    sender_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    receiver_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    status:Mapped[FriendRequestStatus]=mapped_column(Enum(FriendRequestStatus),default=FriendRequestStatus.PENDING)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Friendship(Base):
    __tablename__="friendship"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    friend_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("user.id"))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

# FriendRequest отвечает за заявки, а Friendship отвечает за уже состоящих в дружбе пользователей.