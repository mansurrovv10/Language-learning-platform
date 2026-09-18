from uuid import UUID
from pydantic import BaseModel

class FriendRequestCreate(BaseModel):
    username: str

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: UUID
    receiver_id: UUID
    status: str

class FriendResponse(BaseModel):
    id: UUID
    username: str