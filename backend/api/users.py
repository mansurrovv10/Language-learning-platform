import uuid
from pathlib import Path
from fastapi import APIRouter,Depends,File,HTTPException,UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import SessionLocal
from backend.models.user import UserProfile
from backend.schemas.auth_schema import UserResponseSchema
from backend.schemas.user_schema import UserUpdateSchema, RoleUpdateSchema, ActiveUpdateSchema
from backend.schemas.public_schema import PublicUserSchema
from backend.api.auth import get_current_user,require_admin
from backend.api.chat_ws import manager
from backend.services.user_ser import UserService
from backend.services.account_service import AccountService

user_router=APIRouter(prefix="/users",tags=["Users"])

async def get_db():
    async with SessionLocal() as db:
        yield db

@user_router.get("/me",response_model=UserResponseSchema)
async def user_me(current_user:UserProfile=Depends(get_current_user)):
    return current_user

@user_router.get("/",response_model=list[UserResponseSchema])
async def user_list(db:AsyncSession=Depends(get_db),current_user:UserProfile=Depends(require_admin)):
    return await UserService(db).get_users()

@user_router.get("/search",response_model=list[PublicUserSchema])
async def search_users(q: str,db: AsyncSession = Depends(get_db),
         current_user: UserProfile = Depends(get_current_user)):
    return await UserService(db).search_users(q)

@user_router.get("/{user_id}/public",response_model=PublicUserSchema)
async def user_public(user_id:uuid.UUID,db:AsyncSession=Depends(get_db),
                      current_user:UserProfile=Depends(get_current_user)):
    user=await UserService(db).get_user(user_id)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    return user

@user_router.get("/{user_id}",response_model=UserResponseSchema)
async def user_detail(user_id:uuid.UUID,db:AsyncSession=Depends(get_db),
                      current_user:UserProfile=Depends(get_current_user)):
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    user=await UserService(db).get_user(user_id)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    return user

@user_router.put("/me",response_model=UserResponseSchema)
async def update_profile(data:UserUpdateSchema,current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return await UserService(db).update_user(current_user,data)

@user_router.delete("/me")
async def delete_profile(current_user:UserProfile=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    await AccountService(db).deactivate(current_user.id)
    await manager.disconnect_user(current_user.id)
    return {"message":"User deactivated successfully"}


@user_router.patch("/{user_id}/role",response_model=UserResponseSchema)
async def change_role(user_id:uuid.UUID,data:RoleUpdateSchema,db:AsyncSession=Depends(get_db),
    current_user:UserProfile=Depends(require_admin)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400,detail="You cannot change your own role")

    user=await UserService(db).set_role(user_id,data.role)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    if not data.is_active:
        await manager.disconnect_user(user_id)

    return user


@user_router.patch("/{user_id}/active",response_model=UserResponseSchema)
async def set_active(user_id:uuid.UUID,data:ActiveUpdateSchema,
    db:AsyncSession=Depends(get_db),current_user:UserProfile=Depends(require_admin)):
    if current_user.id == user_id and not data.is_active:
        raise HTTPException(status_code=400,detail="You cannot deactivate yourself")

    user=await UserService(db).set_active(user_id,data.is_active)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    return user


@user_router.patch("/me/avatar",response_model=UserResponseSchema)
async def upload_avatar(file: UploadFile=File(...),
                        current_user:UserProfile=Depends(get_current_user),
                        db:AsyncSession=Depends(get_db)):

    try:
        await AccountService(db).save_avatar(
            current_user,file,Path("uploads/avatars")
        )
    except ValueError as error:
        code = str(error)
        status_code = 413 if code == "AVATAR_TOO_LARGE" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"code":code,"message":code.replace("_"," ").title()},
        )

    return current_user
