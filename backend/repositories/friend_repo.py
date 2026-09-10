from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.social import FriendRequest,Friendship,FriendRequestStatus

class FriendRepository:
    def __init__(self,db:AsyncSession):
        self.db=db

    async def get_request(self,sender_id,receiver_id):
        result=await self.db.execute(select(FriendRequest).where(FriendRequest.sender_id==sender_id,FriendRequest.receiver_id==receiver_id))
        return result.scalar_one_or_none()

    async def get_request_by_id(self,request_id):
        result=await self.db.execute(select(FriendRequest).where(FriendRequest.id==request_id))
        return result.scalar_one_or_none()

    async def create_request(self,request):
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_received_requests(self,user_id):
        result=await self.db.execute(select(FriendRequest).where(FriendRequest.receiver_id==user_id,FriendRequest.status==FriendRequestStatus.PENDING))
        return result.scalars().all()

    async def get_friendship(self,user_id,friend_id):
        result=await self.db.execute(select(Friendship).where(Friendship.user_id==user_id,Friendship.friend_id==friend_id))
        return result.scalar_one_or_none()

    async def get_friends(self,user_id):
        result=await self.db.execute(select(Friendship).where(Friendship.user_id==user_id))
        return result.scalars().all()

    async def create_friendship(self,friendship):
        self.db.add(friendship)
        await self.db.commit()
        await self.db.refresh(friendship)
        return friendship

    async def delete_friendship(self,friendship):
        await self.db.delete(friendship)
        await self.db.commit()

    async def save_request(self,request):
        await self.db.commit()
        await self.db.refresh(request)
        return request