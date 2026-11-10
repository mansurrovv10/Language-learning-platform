import uuid
from datetime import datetime, timedelta

from backend.repositories.review_repo import ReviewRepository
from backend.schemas.page_schema import Page
from backend.schemas.review_schema import DueReviewItem
from backend.time import as_utc, utc_now

REVIEW_INTERVAL_DAYS = (1, 3, 7, 14, 30)


class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    async def record_result(
        self,
        user_id: uuid.UUID,
        exercise_id: int,
        correct: bool,
        at: datetime | None = None,
        commit: bool = False,
    ):
        instant = utc_now() if at is None else as_utc(at)
        item = await self.repository.get_or_create(user_id, exercise_id)
        item.attempts += 1
        item.last_result = correct
        item.updated_at = instant
        if correct:
            item.box = min(5, item.box + 1)
            item.correct_streak += 1
            item.due_at = instant + timedelta(
                days=REVIEW_INTERVAL_DAYS[item.box - 1]
            )
        else:
            item.box = 0
            item.correct_streak = 0
            item.due_at = instant
        return await self.repository.save(item, commit=commit)

    async def get_due(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        at: datetime | None = None,
    ) -> Page[DueReviewItem]:
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("INVALID_PAGINATION")
        instant = utc_now() if at is None else as_utc(at)
        rows, total = await self.repository.get_due(
            user_id, instant, limit, offset
        )
        return Page[DueReviewItem](
            items=[
                DueReviewItem(
                    exercise_id=exercise.id,
                    exercise_type=exercise.type,
                    question=exercise.question,
                    options=exercise.options,
                    box=item.box,
                    due_at=item.due_at,
                    last_result=item.last_result,
                    attempts=item.attempts,
                )
                for item, exercise in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
