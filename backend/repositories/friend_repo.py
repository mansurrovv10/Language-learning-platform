from sqlalchemy.orm import Session
from backend.models.social import FriendRequest,Friendship,FriendRequestStatus

class FriendRepository:
    def __init__(self,db:Session):
        self.db=db

    def get_request(self,sender_id,receiver_id):
        return self.db.query(FriendRequest).filter(FriendRequest.sender_id==sender_id,FriendRequest.receiver_id==receiver_id).first()

    def get_request_by_id(self,request_id):
        return self.db.query(FriendRequest).filter(FriendRequest.id==request_id).first()

    def create_request(self,request):
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_received_requests(self,user_id):
        return self.db.query(FriendRequest).filter(FriendRequest.receiver_id==user_id,FriendRequest.status==FriendRequestStatus.PENDING).all()

    def get_friendship(self,user_id,friend_id):
        return self.db.query(Friendship).filter(Friendship.user_id==user_id,Friendship.friend_id==friend_id).first()

    def get_friends(self,user_id):
        return self.db.query(Friendship).filter(Friendship.user_id==user_id).all()

    def create_friendship(self,friendship):
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def delete_friendship(self,friendship):
        self.db.delete(friendship)
        self.db.commit()

    def save_request(self,request):
        self.db.commit()
        self.db.refresh(request)
        return request