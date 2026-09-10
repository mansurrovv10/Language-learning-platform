from sqlalchemy.orm import Session
from backend.models.user import UserProfile

class UserRepository:
    def __init__(self,db:Session):
        self.db=db

    def get_by_id(self,user_id):
        return self.db.query(UserProfile).filter(UserProfile.id==user_id).first()

    def get_by_email(self,email):
        return self.db.query(UserProfile).filter(UserProfile.email==email).first()

    def get_by_username(self,username):
        return self.db.query(UserProfile).filter(UserProfile.username==username).first()

    def get_all(self):
        return self.db.query(UserProfile).all()

    def create(self,user):
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self,user):
        self.db.delete(user)
        self.db.commit()