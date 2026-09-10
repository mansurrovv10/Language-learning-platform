import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.review import CourseReview


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(select(CourseReview))
        return result.scalars().all()

    async def get_by_id(self, review_id: int):
        result = await self.session.execute(
            select(CourseReview).where(CourseReview.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID):
        result = await self.session.execute(
            select(CourseReview).where(CourseReview.user_id == user_id)
        )
        return result.scalars().all()

    async def create(self, data):
        review = CourseReview(
            user_id=data.user_id,
            course_id=data.course_id,
            rating=data.rating,
            comment=data.comment,
            created_at=datetime.utcnow()
        )
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def update(self, review_id: int, data):
        review = await self.get_by_id(review_id)

        if not review:
            return None

        if data.rating is not None:
            review.rating = data.rating

        if data.comment is not None:
            review.comment = data.comment

        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def delete(self, review_id: int):
        review = await self.get_by_id(review_id)

        if not review:
            return False

        await self.session.delete(review)
        await self.session.commit()
        return True