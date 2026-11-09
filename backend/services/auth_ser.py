import uuid
from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from backend.models.user import UserProfile,RefreshToken
from backend.repositories.auth_repo import AuthRepository
from backend.config import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_LIFETIME,REFRESH_TOKEN_LIFETIME

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

class AuthService:
    def __init__(self,db):
        self.repository=AuthRepository(db)

    def get_password_hash(self,password):
        return pwd_context.hash(password)

    def verify_password(self,password,hashed_password):
        return pwd_context.verify(password,hashed_password)

    def create_access_token(self,user_id):
        expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_LIFETIME)
        data={"sub":str(user_id),"type":"access","exp":expire}
        return jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)

    def create_refresh_token(self,user_id):
        expire=datetime.now(timezone.utc)+timedelta(days=REFRESH_TOKEN_LIFETIME)
        data={"sub":str(user_id),"type":"refresh","exp":expire}
        return jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)

    def decode_token(self,token):
        try:
            return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        except JWTError:
            return None

    async def register(self, email, username, password):
        email = email.lower().strip()
        username = username.strip()

        if await self.repository.get_user_by_username(username):
            raise HTTPException(status_code=400, detail={
                "code":"USERNAME_EXISTS",
                "message":"Username already exists"
            })

        if await self.repository.get_user_by_email(email):
            raise HTTPException(status_code=400, detail={
                "code":"EMAIL_EXISTS",
                "message":"Email already exists"
            })

        user = UserProfile(
            email=email,
            username=username,
            password_hash=self.get_password_hash(password))

        try:
            return await self.repository.create_user(user)
        except IntegrityError:
            await self.repository.db.rollback()
            raise HTTPException(status_code=400, detail={
                "code":"USER_CONFLICT",
                "message":"Email or username already exists"
            })


    async def login(self, email, password):
        email = email.lower().strip()
        user = await self.repository.get_user_by_email(email)

        if not user or not self.verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403,detail="User is inactive")

        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)

        refresh_db = RefreshToken(users_id=user.id, token=refresh_token)
        await self.repository.create_refresh_token(refresh_db)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def logout(self,token):
        refresh_token=await self.repository.get_refresh_token(token)
        if not refresh_token:
            raise HTTPException(status_code=401,detail="Invalid refresh token")
        await self.repository.delete_refresh_token(refresh_token)

    async def refresh(self, token):
        refresh_token = await self.repository.get_refresh_token(token)
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        payload = self.decode_token(token)
        if not payload:
            await self.repository.delete_refresh_token(refresh_token)
            raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Refresh token required")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            user = await self.repository.get_user_by_id(uuid.UUID(user_id))
        except (TypeError,ValueError):
            user = None
        if not user or not user.is_active:
            await self.repository.delete_refresh_token(refresh_token)
            raise HTTPException(status_code=403,detail="User is inactive")

        await self.repository.delete_refresh_token(refresh_token)

        new_access_token = self.create_access_token(user_id)
        new_refresh_token = self.create_refresh_token(user_id)

        new_refresh_db = RefreshToken(
            users_id=uuid.UUID(user_id),
            token=new_refresh_token
        )
        await self.repository.create_refresh_token(new_refresh_db)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
