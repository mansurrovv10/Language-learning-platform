import uuid
from datetime import datetime

from pydantic import BaseModel

from backend.models.chat import ChatType


class ChatCreate(BaseModel):
    type: ChatType
    language_id: int | None = None


class ChatResponse(BaseModel):
    id: uuid.UUID
    type: ChatType
    language_id: int | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ChatMemberCreate(BaseModel):
    user_id: uuid.UUID


class ChatMemberResponse(BaseModel):
    chat_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime

    model_config = {
        "from_attributes": True
    }