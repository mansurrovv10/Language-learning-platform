import uuid

from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user,require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.schemas.achievement_schema import (
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
    UserAchievementResponse
)
from backend.services.achievement_service import AchievementService


router = APIRouter(prefix="/achievements",tags=["Achievements"])


def get_achievement_service(
    session: AsyncSession = Depends(get_session)
):
    repository = AchievementRepository(session)
    gamification_repository = GamificationRepository(session)

    return AchievementService(repository,gamification_repository)


@router.get("",response_model=list[AchievementResponse])
async def get_achievements(
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_all()


@router.get("/user/{user_id}",response_model=list[UserAchievementResponse])
async def get_user_achievements(
    user_id: uuid.UUID,
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.get_user_achievements(user_id)


@router.post("/{achievement_id}/award/{user_id}",response_model=UserAchievementResponse)
async def award_achievement(
    achievement_id: int,
    user_id: uuid.UUID,
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(require_admin)
):
    user_achievement = await service.check_and_award(user_id,achievement_id)

    if not user_achievement:
        raise HTTPException(status_code=404,detail="Achievement not found")

    return user_achievement


@router.get("/{achievement_id}",response_model=AchievementResponse)
async def get_achievement(
    achievement_id: int,
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(get_current_user)
):
    achievement = await service.get_by_id(achievement_id)

    if not achievement:
        raise HTTPException(status_code=404,detail="Achievement not found")

    return achievement


@router.post("",response_model=AchievementResponse)
async def create_achievement(
    data: AchievementCreate,
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(require_admin)
):
    return await service.create(data)


@router.put("/{achievement_id}",response_model=AchievementResponse)
async def update_achievement(
    achievement_id: int,
    data: AchievementUpdate,
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(require_admin)
):
    achievement = await service.update(achievement_id,data)

    if not achievement:
        raise HTTPException(status_code=404,detail="Achievement not found")

    return achievement


@router.delete("/{achievement_id}")
async def delete_achievement(
    achievement_id: int,
    service: AchievementService = Depends(get_achievement_service),
    current_user: UserProfile = Depends(require_admin)
):
    result = await service.delete(achievement_id)

    if not result:
        raise HTTPException(status_code=404,detail="Achievement not found")

    return {"message":"Achievement deleted"}