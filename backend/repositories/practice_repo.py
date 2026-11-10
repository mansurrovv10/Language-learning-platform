import uuid
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.exercise import Exercise
from backend.models.practice import PracticeSession, PracticeSessionItem
from backend.models.review_item import ReviewItem
from backend.models.user import UserProfile


class PracticeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def lock_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            select(UserProfile.id)
            .where(UserProfile.id == user_id)
            .with_for_update()
        )

    async def get_active(
        self, user_id: uuid.UUID, at: datetime
    ) -> PracticeSession | None:
        return await self.session.scalar(
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user_id,
                PracticeSession.completed_at.is_(None),
                PracticeSession.expires_at > at,
            )
            .order_by(PracticeSession.created_at.desc())
            .limit(1)
        )

    async def get_candidates(
        self, user_id: uuid.UUID, at: datetime, limit: int = 3
    ) -> list[Exercise]:
        return list(
            await self.session.scalars(
                select(Exercise)
                .join(ReviewItem, ReviewItem.exercise_id == Exercise.id)
                .where(
                    ReviewItem.user_id == user_id,
                    or_(ReviewItem.due_at <= at, ReviewItem.last_result.is_(False)),
                )
                .order_by(ReviewItem.due_at, ReviewItem.exercise_id)
                .limit(limit)
            )
        )

    async def get_items(
        self, session_id: uuid.UUID
    ) -> list[PracticeSessionItem]:
        return list(
            await self.session.scalars(
                select(PracticeSessionItem)
                .where(PracticeSessionItem.session_id == session_id)
                .order_by(PracticeSessionItem.position)
            )
        )

    async def lock_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> PracticeSession | None:
        return await self.session.scalar(
            select(PracticeSession)
            .where(
                PracticeSession.id == session_id,
                PracticeSession.user_id == user_id,
            )
            .with_for_update()
        )
