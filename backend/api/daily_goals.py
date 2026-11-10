from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.daily_goal_repo import DailyGoalRepository
from backend.schemas.daily_goal_schema import DailyGoalStatus, DailyGoalUpdate
from backend.services.daily_goal_service import DailyGoalService

router = APIRouter(prefix="/daily-goal", tags=["Daily goal"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]


def get_daily_goal_service(session: SessionDep) -> DailyGoalService:
    return DailyGoalService(DailyGoalRepository(session))


ServiceDep = Annotated[DailyGoalService, Depends(get_daily_goal_service)]


@router.get("", response_model=DailyGoalStatus)
async def get_daily_goal(
    current_user: CurrentUser,
    service: ServiceDep,
):
    return await service.get_status(current_user.id)


@router.put("", response_model=DailyGoalStatus)
async def update_daily_goal(
    data: DailyGoalUpdate,
    current_user: CurrentUser,
    service: ServiceDep,
):
    return await service.set_target(current_user.id, data.target_xp)
