from backend.models.user import UserProfile
from backend.api.auth import get_password_hash
from backend.repositories.user_repo import UserRepository

class UserService:
    def __init__(self,db):
        self.repository=UserRepository(db)

    def get_user(self,user_id):
        return self.repository.get_by_id(user_id)

    def get_users(self):
        return self.repository.get_all()

    def update_user(self,user,data):
        update_data=data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password"]=get_password_hash(update_data["password"])
        for key,value in update_data.items():
            setattr(user,key,value)
        self.repository.db.commit()
        self.repository.db.refresh(user)
        return user

    def delete_user(self,user):
        self.repository.delete(user)