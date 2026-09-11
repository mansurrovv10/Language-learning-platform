import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.gamification_repo import GamificationRepository
from backend.schemas.gamification_schema import XPHistoryResponse, StreakResponse
from backend.services.gamification_service import GamificationService


router = APIRouter(prefix="/gamification",tags=["Gamification"])


def get_gamification_service(session: AsyncSession = Depends(get_session)):
    repository = GamificationRepository(session)
    return GamificationService(repository)


@router.get("/xp/{user_id}",response_model=list[XPHistoryResponse])
async def get_xp_history(
    user_id: uuid.UUID,
    service: GamificationService = Depends(get_gamification_service),
    current_user: UserProfile = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.get_xp_history(user_id)


@router.get("/streak/{user_id}",response_model=StreakResponse)
async def get_streak(
    user_id: uuid.UUID,
    service: GamificationService = Depends(get_gamification_service),
    current_user: UserProfile = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    streak = await service.get_streak(user_id)

    if not streak:
        raise HTTPException(status_code=404,detail="Streak not found")

    return streak