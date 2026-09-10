import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.repositories.review_repo import ReviewRepository
from backend.schemas.review_schema import ReviewCreate, ReviewUpdate, ReviewResponse
from backend.services.review_service import ReviewService


router = APIRouter(prefix="/reviews", tags=["Reviews"])


def get_review_service(session: AsyncSession = Depends(get_session)):
    repository = ReviewRepository(session)
    return ReviewService(repository)


@router.get("", response_model=list[ReviewResponse])
async def get_reviews(
    service: ReviewService = Depends(get_review_service)
):
    return await service.get_all()


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service)
):
    review = await service.get_by_id(review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(
    user_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service)
):
    return await service.get_by_user(user_id)


@router.post("", response_model=ReviewResponse)
async def create_review(
    data: ReviewCreate,
    service: ReviewService = Depends(get_review_service)
):
    return await service.create(data)


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    service: ReviewService = Depends(get_review_service)
):
    review = await service.update(review_id, data)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service)
):
    result = await service.delete(review_id)

    if not result:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"message": "Review deleted"}