from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user,require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.challenge_repo import ChallengeRepository
from backend.schemas.challenge_schema import (
    ChallengeCreate,
    ChallengeUpdate,
    ChallengeResponse
)
from backend.services.challenge_service import ChallengeService


router = APIRouter(prefix="/challenges",tags=["Challenges"])


def get_challenge_service(
    session: AsyncSession = Depends(get_session)
):
    repository = ChallengeRepository(session)

    return ChallengeService(repository)


@router.get("",response_model=list[ChallengeResponse])
async def get_challenges(
    service: ChallengeService = Depends(get_challenge_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_all()


@router.get("/today",response_model=ChallengeResponse)
async def get_today_challenge(
    service: ChallengeService = Depends(get_challenge_service),
    current_user: UserProfile = Depends(get_current_user)
):
    challenge = await service.get_today()

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Today's challenge not found"
        )

    return challenge


@router.get("/{challenge_id}",response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: int,
    service: ChallengeService = Depends(get_challenge_service),
    current_user: UserProfile = Depends(get_current_user)
):
    challenge = await service.get_by_id(challenge_id)

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found"
        )

    return challenge


@router.post("",response_model=ChallengeResponse)
async def create_challenge(
    data: ChallengeCreate,
    service: ChallengeService = Depends(get_challenge_service),
    current_user: UserProfile = Depends(require_admin)
):
    challenge = await service.create(data)

    if not challenge:
        raise HTTPException(
            status_code=400,
            detail="Challenge for this date already exists"
        )

    return challenge


@router.put("/{challenge_id}",response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: int,
    data: ChallengeUpdate,
    service: ChallengeService = Depends(get_challenge_service),
    current_user: UserProfile = Depends(require_admin)
):
    challenge = await service.update(
        challenge_id,
        data
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found"
        )

    return challenge


@router.delete("/{challenge_id}")
async def delete_challenge(
    challenge_id: int,
    service: ChallengeService = Depends(get_challenge_service),
    current_user: UserProfile = Depends(require_admin)
):
    result = await service.delete(challenge_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found"
        )

    return {"message":"Challenge deleted"}