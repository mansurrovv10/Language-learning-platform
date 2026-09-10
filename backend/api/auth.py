import uuid
from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.db import SessionLocal
from backend.models.user import UserProfile,UserRole
from backend.schemas.auth_schema import RegisterSchema,LoginSchema,TokenSchema,RefreshSchema,UserResponseSchema
from backend.services.auth_ser import AuthService

auth_router=APIRouter(prefix="/auth",tags=["Auth"])
security=HTTPBearer()

async def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

@auth_router.post("/register",response_model=UserResponseSchema)
async def register(user:RegisterSchema,db:Session=Depends(get_db)):
    return AuthService(db).register(user.email,user.username,user.password)

@auth_router.post("/login",response_model=TokenSchema)
async def login(user:LoginSchema,db:Session=Depends(get_db)):
    return AuthService(db).login(user.email,user.password)

@auth_router.post("/logout")
async def logout(data:RefreshSchema,db:Session=Depends(get_db)):
    AuthService(db).logout(data.refresh_token)
    return {"message":"Logout successful"}

@auth_router.post("/refresh")
async def refresh(data:RefreshSchema,db:Session=Depends(get_db)):
    return AuthService(db).refresh(data.refresh_token)

async def get_current_user(credentials:HTTPAuthorizationCredentials=Depends(security),db:Session=Depends(get_db)):
    service=AuthService(db)
    payload=service.decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401,detail="Invalid or expired token")
    if payload.get("type")!="access":
        raise HTTPException(status_code=401,detail="Access token required")
    user_id=payload.get("sub")
    try:
        user_uuid=uuid.UUID(user_id)
    except (ValueError,TypeError):
        raise HTTPException(status_code=401,detail="Invalid user ID")
    user=db.query(UserProfile).filter(UserProfile.id==user_uuid).first()
    if not user:
        raise HTTPException(status_code=404,detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403,detail="User is inactive")
    return user

def require_admin(current_user:UserProfile=Depends(get_current_user)):
    if current_user.role!=UserRole.ADMIN:
        raise HTTPException(status_code=403,detail="Admin role required")
    return current_user