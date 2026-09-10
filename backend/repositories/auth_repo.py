from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import UserProfile,RefreshToken

class AuthRepository:
    def __init__(self,db:AsyncSession):
        self.db=db

    async def get_user_by_email(self,email):
        result=await self.db.execute(select(UserProfile).where(UserProfile.email==email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self,username):
        result=await self.db.execute(select(UserProfile).where(UserProfile.username==username))
        return result.scalar_one_or_none()

    async def get_refresh_token(self,token):
        result=await self.db.execute(select(RefreshToken).where(RefreshToken.token==token))
        return result.scalar_one_or_none()

    async def create_user(self,user):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_refresh_token(self,refresh_token):
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def delete_refresh_token(self,refresh_token):
        await self.db.delete(refresh_token)
        await self.db.commit()