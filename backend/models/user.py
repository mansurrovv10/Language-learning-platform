import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List
from sqlalchemy import String, Boolean, DateTime, Enum, Integer,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"


class UserProfile(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole),default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    refresh_user: Mapped[List['RefreshToken']] = relationship(back_populates='users',
                                                              cascade='all, delete-orphan')

class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    users_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('user.id'))
    users: Mapped[UserProfile] = relationship(back_populates='refresh_user')
    token: Mapped[str] = mapped_column(String, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)