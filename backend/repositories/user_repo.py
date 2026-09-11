from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import UserProfile

class UserRepository:
    def __init__(self,db:AsyncSession):
        self.db=db

    async def get_by_id(self,user_id):
        result=await self.db.execute(select(UserProfile).where(UserProfile.id==user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self,email):
        result=await self.db.execute(select(UserProfile).where(UserProfile.email==email))
        return result.scalar_one_or_none()

    async def get_by_username(self,username):
        result=await self.db.execute(select(UserProfile).where(UserProfile.username==username))
        return result.scalar_one_or_none()

    async def get_all(self):
        result=await self.db.execute(select(UserProfile))
        return result.scalars().all()

    async def create(self,user):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self,user):
        await self.db.delete(user)
        await self.db.commit()

    async def set_role(self,user,role):
        user.role=role
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_active(self,user,is_active):
        user.is_active=is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user