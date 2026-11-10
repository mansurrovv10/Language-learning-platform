import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.exercise import Exercise
from backend.models.review_item import ReviewItem
from backend.time import utc_now


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self, user_id: uuid.UUID, exercise_id: int
    ) -> ReviewItem:
        now = utc_now()
        await self.session.execute(
            pg_insert(ReviewItem)
            .values(
                user_id=user_id,
                exercise_id=exercise_id,
                box=0,
                due_at=now,
                attempts=0,
                correct_streak=0,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "exercise_id"])
        )
        return (
            await self.session.scalars(
                select(ReviewItem)
                .where(
                    ReviewItem.user_id == user_id,
                    ReviewItem.exercise_id == exercise_id,
                )
                .with_for_update()
            )
        ).one()

    async def save(self, item: ReviewItem, commit: bool = True) -> ReviewItem:
        self.session.add(item)
        if commit:
            await self.session.commit()
            await self.session.refresh(item)
        else:
            await self.session.flush()
        return item

    async def get_due(
        self,
        user_id: uuid.UUID,
        at: datetime,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[ReviewItem, Exercise]], int]:
        filters = (ReviewItem.user_id == user_id, ReviewItem.due_at <= at)
        total = int(
            await self.session.scalar(
                select(func.count()).select_from(ReviewItem).where(*filters)
            )
            or 0
        )
        rows = (
            await self.session.execute(
                select(ReviewItem, Exercise)
                .join(Exercise, Exercise.id == ReviewItem.exercise_id)
                .where(*filters)
                .order_by(ReviewItem.due_at, ReviewItem.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return list(rows), total
