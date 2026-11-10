import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.practice_repo import PracticeRepository
from backend.schemas.practice_schema import (
    PracticeCompletion,
    PracticeResult,
    PracticeSessionResponse,
)
from backend.services.practice_service import PracticeError, PracticeService

router = APIRouter(prefix="/practice", tags=["Practice"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]


def get_practice_service(session: SessionDep) -> PracticeService:
    return PracticeService(
        PracticeRepository(session), GamificationRepository(session)
    )


ServiceDep = Annotated[PracticeService, Depends(get_practice_service)]


def _practice_http_error(error: PracticeError) -> HTTPException:
    code = str(error)
    status = 404 if code == "PRACTICE_NOT_FOUND" else 409
    if code == "PRACTICE_ANSWERS_INVALID":
        status = 422
    return HTTPException(
        status_code=status,
        detail={"code": code, "message": code.replace("_", " ").title()},
    )


@router.post("/sessions", response_model=PracticeSessionResponse)
async def create_practice_session(
    current_user: CurrentUser, service: ServiceDep
):
    try:
        return await service.create_session(current_user.id)
    except PracticeError as error:
        raise _practice_http_error(error)


@router.post("/sessions/{session_id}/complete", response_model=PracticeResult)
async def complete_practice_session(
    session_id: uuid.UUID,
    data: PracticeCompletion,
    current_user: CurrentUser,
    service: ServiceDep,
):
    try:
        return await service.complete_session(current_user.id, session_id, data)
    except PracticeError as error:
        raise _practice_http_error(error)
