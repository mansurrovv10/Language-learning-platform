from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import get_session
from backend.repositories.gamification import GamificationRepository
from backend.schemas.gamification import XPCreate, XPResponse, StreakResponse
from backend.services.gamification import GamificationService


router = APIRouter(prefix="/gamification", tags=["Gamification"])


def get_gamification_service(session: AsyncSession = Depends(get_session)):
    repository = GamificationRepository(session)
    return GamificationService(repository)


@router.get("/xp/{user_id}", response_model=list[XPResponse])
async def get_xp_history(
    user_id: int,
    service: GamificationService = Depends(get_gamification_service)
):
    return await service.get_xp_history(user_id)


@router.post("/xp", response_model=XPResponse)
async def add_xp(
    data: XPCreate,
    service: GamificationService = Depends(get_gamification_service)
):
    return await service.add_xp(data)


@router.get("/streak/{user_id}", response_model=StreakResponse)
async def get_streak(
    user_id: int,
    service: GamificationService = Depends(get_gamification_service)
):
    streak = await service.get_streak(user_id)

    if not streak:
        raise HTTPException(status_code=404, detail="Streak not found")

    return streak


@router.post("/streak/{user_id}", response_model=StreakResponse)
async def update_streak(
    user_id: int,
    service: GamificationService = Depends(get_gamification_service)
):
    return await service.update_streak(user_id)