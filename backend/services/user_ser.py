from backend.services.auth_ser import pwd_context
from backend.repositories.user_repo import UserRepository

class UserService:
    def __init__(self,db):
        self.repository=UserRepository(db)

    async def get_user(self,user_id):
        return await self.repository.get_by_id(user_id)

    async def get_users(self):
        return await self.repository.get_all()

    async def update_user(self,user,data):
        update_data=data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"]=pwd_context.hash(update_data.pop("password"))
        for key,value in update_data.items():
            setattr(user,key,value)
        await self.repository.db.commit()
        await self.repository.db.refresh(user)
        return user

    async def delete_user(self,user):
        await self.repository.delete(user)

    async def set_role(self,user_id,role):
        user=await self.repository.get_by_id(user_id)

        if not user:
            return None

        return await self.repository.set_role(user,role)

    async def set_active(self,user_id,is_active):
        user=await self.repository.get_by_id(user_id)

        if not user:
            return None

        return await self.repository.set_active(user,is_active)

    async def deactivate_user(self,user_id):
        user=await self.repository.get_by_id(user_id)

        if not user:
            return None

        return await self.repository.set_active(user,False)