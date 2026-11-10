from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.review_repo import ReviewRepository
from backend.schemas.page_schema import Page
from backend.schemas.review_schema import DueReviewItem
from backend.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]


def get_review_service(session: SessionDep) -> ReviewService:
    return ReviewService(ReviewRepository(session))


ServiceDep = Annotated[ReviewService, Depends(get_review_service)]


@router.get("/due", response_model=Page[DueReviewItem])
async def get_due_reviews(
    current_user: CurrentUser,
    service: ServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await service.get_due(current_user.id, limit=limit, offset=offset)
