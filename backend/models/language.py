from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class Language(Base):
    __tablename__ = "language"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    code: Mapped[str] = mapped_column(String,unique=True)
    name: Mapped[str] = mapped_column(String,unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean,default=False)