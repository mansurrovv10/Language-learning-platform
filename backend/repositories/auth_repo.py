from sqlalchemy.orm import Session
from backend.models.user import UserProfile,RefreshToken

class AuthRepository:
    def __init__(self,db:Session):
        self.db=db

    def get_user_by_email(self,email):
        return self.db.query(UserProfile).filter(UserProfile.email==email).first()

    def get_user_by_username(self,username):
        return self.db.query(UserProfile).filter(UserProfile.username==username).first()

    def get_refresh_token(self,token):
        return self.db.query(RefreshToken).filter(RefreshToken.token==token).first()

    def create_user(self,user):
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_refresh_token(self,refresh_token):
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def delete_refresh_token(self,refresh_token):
        self.db.delete(refresh_token)
        self.db.commit()