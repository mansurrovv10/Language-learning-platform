import uuid
from datetime import datetime

from pydantic import BaseModel,ConfigDict

from backend.models.chat import ChatType


class ChatCreate(BaseModel):
    type: ChatType
    language_id: int | None = None


class ChatResponse(BaseModel):
    id: uuid.UUID
    type: ChatType
    language_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMemberCreate(BaseModel):
    user_id: uuid.UUID


class ChatMemberResponse(BaseModel):
    chat_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str


class MessageUpdate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


class ReactionCreate(BaseModel):
    reaction: str


class ReactionResponse(BaseModel):
    id: int
    message_id: uuid.UUID
    user_id: uuid.UUID
    reaction: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)