from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import SessionLocal
from backend.models.user import UserProfile
from backend.schemas.friend_schema import FriendRequestCreate,FriendRequestResponse,FriendResponse
from backend.services.friend_ser import FriendService
from backend.api.auth import get_current_user

friend_router=APIRouter(prefix="/friends",tags=["Friends"])

async def get_db():
    async with SessionLocal() as db:
        yield db

@friend_router.post("/request",response_model=FriendRequestResponse)
async def send_request(data:FriendRequestCreate,current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await FriendService(db).send_request(current_user.id,data.receiver_id)

@friend_router.post("/request/{request_id}/accept",response_model=FriendRequestResponse)
async def accept_request(request_id:int,current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await FriendService(db).accept_request(request_id,current_user.id)

@friend_router.post("/request/{request_id}/reject",response_model=FriendRequestResponse)
async def reject_request(request_id:int,current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await FriendService(db).reject_request(request_id,current_user.id)

@friend_router.get("/requests",response_model=list[FriendRequestResponse])
async def list_requests(current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await FriendService(db).get_requests(current_user.id)

@friend_router.get("/",response_model=list[FriendResponse])
async def friends_list(current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await FriendService(db).get_friends(current_user.id)

@friend_router.delete("/{friend_id}")
async def remove_friend(friend_id:str,current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await FriendService(db).remove_friend(current_user.id,friend_id)