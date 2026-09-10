from uuid import UUID
from pydantic import BaseModel

class FriendRequestCreate(BaseModel):
    receiver_id:UUID

class FriendRequestResponse(BaseModel):
    id:int
    sender_id:UUID
    receiver_id:UUID
    status:str

class FriendResponse(BaseModel):
    id:UUID
    username:str