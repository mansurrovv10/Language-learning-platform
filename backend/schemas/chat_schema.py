import uuid
from datetime import datetime

from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator

from backend.models.chat import ChatType
from backend.schemas.public_schema import PublicUserSchema


class ChatCreate(BaseModel):
    type: ChatType = ChatType.PRIVATE
    language_id: int | None = None
    participant_username: str = Field(min_length=1,max_length=100)

    @field_validator("participant_username",mode="before")
    @classmethod
    def strip_participant_username(cls,value):
        return value.strip() if isinstance(value,str) else value

    @model_validator(mode="after")
    def private_only(self):
        if self.type != ChatType.PRIVATE:
            raise ValueError("GROUP_CHAT_DISABLED")
        return self


class ChatResponse(BaseModel):
    id: uuid.UUID
    type: ChatType
    language_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMemberCreate(BaseModel):
    username: str


class ChatMemberResponse(BaseModel):
    chat_id: uuid.UUID
    user_id: uuid.UUID
    user: PublicUserSchema
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1,max_length=2000)

    @field_validator("content",mode="before")
    @classmethod
    def strip_content(cls,value):
        return value.strip() if isinstance(value,str) else value


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1,max_length=2000)

    @field_validator("content",mode="before")
    @classmethod
    def strip_content(cls,value):
        return value.strip() if isinstance(value,str) else value


class MessageResponse(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    sender: PublicUserSchema
    content: str
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)
