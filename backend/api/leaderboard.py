import uuid

from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user,require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.leaderboard_repo import LeaderboardRepository
from backend.schemas.leaderboard_schema import LeaderboardResponse,UserLeaderboardResponse
from backend.services.leaderboard_service import LeaderboardService


router = APIRouter(prefix="/leaderboard",tags=["Leaderboard"])


def get_leaderboard_service(session: AsyncSession = Depends(get_session)):
    repository = LeaderboardRepository(session)
    return LeaderboardService(repository)


@router.get("",response_model=list[LeaderboardResponse])
async def get_leaderboard(
    limit: int = 10,
    service: LeaderboardService = Depends(get_leaderboard_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_leaderboard(limit)


@router.get("/{user_id}",response_model=UserLeaderboardResponse)
async def get_user_rank(
    user_id: uuid.UUID,
    service: LeaderboardService = Depends(get_leaderboard_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_user(user_id)


@router.post("/refresh")
async def refresh_leaderboard(
    service: LeaderboardService = Depends(get_leaderboard_service),
    current_user: UserProfile = Depends(require_admin)
):
    return await service.refresh()