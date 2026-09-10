from fastapi import HTTPException
from backend.models.social import FriendRequest,Friendship,FriendRequestStatus
from backend.models.user import UserProfile
from backend.repositories.friend_repo import FriendRepository

class FriendService:
    def __init__(self,db):
        self.repository=FriendRepository(db)

    def send_request(self,sender_id,receiver_id):
        if sender_id==receiver_id:
            raise HTTPException(status_code=400,detail="You cannot send request to yourself")
        receiver=self.repository.db.query(UserProfile).filter(UserProfile.id==receiver_id).first()
        if not receiver:
            raise HTTPException(status_code=404,detail="User not found")
        if self.repository.get_friendship(sender_id,receiver_id):
            raise HTTPException(status_code=400,detail="Already friends")
        if self.repository.get_request(sender_id,receiver_id):
            raise HTTPException(status_code=400,detail="Request already exists")
        request=FriendRequest(sender_id=sender_id,receiver_id=receiver_id)
        return self.repository.create_request(request)

    def accept_request(self,request_id,user_id):
        request=self.repository.get_request_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404,detail="Request not found")
        if request.receiver_id!=user_id:
            raise HTTPException(status_code=403,detail="You cannot accept this request")
        if request.status!=FriendRequestStatus.PENDING:
            raise HTTPException(status_code=400,detail="Request is not pending")
        request.status=FriendRequestStatus.ACCEPTED
        self.repository.save_request(request)
        self.repository.create_friendship(Friendship(user_id=request.sender_id,friend_id=request.receiver_id))
        self.repository.create_friendship(Friendship(user_id=request.receiver_id,friend_id=request.sender_id))
        return request

    def reject_request(self,request_id,user_id):
        request=self.repository.get_request_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404,detail="Request not found")
        if request.receiver_id!=user_id:
            raise HTTPException(status_code=403,detail="You cannot reject this request")
        if request.status!=FriendRequestStatus.PENDING:
            raise HTTPException(status_code=400,detail="Request is not pending")
        request.status=FriendRequestStatus.REJECTED
        return self.repository.save_request(request)

    def get_requests(self,user_id):
        return self.repository.get_received_requests(user_id)

    def get_friends(self,user_id):
        friendships=self.repository.get_friends(user_id)
        friends=[]
        for friendship in friendships:
            friend=self.repository.db.query(UserProfile).filter(UserProfile.id==friendship.friend_id).first()
            if friend:
                friends.append(friend)
        return friends

    def remove_friend(self,user_id,friend_id):
        friendship1=self.repository.get_friendship(user_id,friend_id)
        friendship2=self.repository.get_friendship(friend_id,user_id)
        if not friendship1:
            raise HTTPException(status_code=404,detail="Friend not found")
        self.repository.delete_friendship(friendship1)
        if friendship2:
            self.repository.delete_friendship(friendship2)
        return {"message":"Friend removed"}