import uuid
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import SessionLocal
from backend.models.user import UserProfile
from backend.schemas.auth_schema import UserResponseSchema
from backend.schemas.user_schema import UserUpdateSchema, RoleUpdateSchema, ActiveUpdateSchema
from backend.api.auth import get_current_user,require_admin
from backend.services.user_ser import UserService

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

@user_router.get("/{user_id}",response_model=UserResponseSchema)
async def user_detail(
    user_id:uuid.UUID,
    db:AsyncSession=Depends(get_db),
    current_user:UserProfile=Depends(get_current_user)
):
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
    await UserService(db).delete_user(current_user)
    return {"message":"User deleted successfully"}


@user_router.patch("/{user_id}/role",response_model=UserResponseSchema)
async def change_role(
    user_id:uuid.UUID,
    data:RoleUpdateSchema,
    db:AsyncSession=Depends(get_db),
    current_user:UserProfile=Depends(require_admin)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400,detail="You cannot change your own role")

    user=await UserService(db).set_role(user_id,data.role)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    return user


@user_router.patch("/{user_id}/active",response_model=UserResponseSchema)
async def set_active(
    user_id:uuid.UUID,
    data:ActiveUpdateSchema,
    db:AsyncSession=Depends(get_db),
    current_user:UserProfile=Depends(require_admin)
):
    if current_user.id == user_id and not data.is_active:
        raise HTTPException(status_code=400,detail="You cannot deactivate yourself")

    user=await UserService(db).set_active(user_id,data.is_active)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    return user


@user_router.delete("/{user_id}")
async def deactivate_user(
    user_id:uuid.UUID,
    db:AsyncSession=Depends(get_db),
    current_user:UserProfile=Depends(require_admin)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400,detail="You cannot deactivate yourself")

    user=await UserService(db).deactivate_user(user_id)

    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    return {"message":"User deactivated"}