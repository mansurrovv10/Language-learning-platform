import uuid
from datetime import date, datetime, time, timedelta, timezone

from backend.repositories.daily_goal_repo import DailyGoalRepository
from backend.schemas.daily_goal_schema import DailyGoalStatus
from backend.time import BISHKEK, as_utc, utc_now


def bishkek_day_bounds(
    at: datetime | None = None,
) -> tuple[datetime, datetime, date]:
    instant = utc_now() if at is None else as_utc(at)
    day = instant.astimezone(BISHKEK).date()
    start_local = datetime.combine(day, time.min, tzinfo=BISHKEK)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
        day,
    )


class DailyGoalService:
    def __init__(self, repository: DailyGoalRepository):
        self.repository = repository

    async def get_status(
        self, user_id: uuid.UUID, at: datetime | None = None
    ) -> DailyGoalStatus:
        start_at, end_at, day = bishkek_day_bounds(at)
        goal = await self.repository.get_or_create(user_id)
        earned_xp = await self.repository.sum_xp(user_id, start_at, end_at)
        remaining_xp = max(0, goal.target_xp - earned_xp)
        return DailyGoalStatus(
            day=day,
            target_xp=goal.target_xp,
            earned_xp=earned_xp,
            remaining_xp=remaining_xp,
            completed=earned_xp >= goal.target_xp,
        )

    async def set_target(
        self, user_id: uuid.UUID, target_xp: int, at: datetime | None = None
    ) -> DailyGoalStatus:
        if not 10 <= target_xp <= 200:
            raise ValueError("DAILY_GOAL_TARGET_INVALID")
        await self.repository.set_target(user_id, target_xp)
        return await self.get_status(user_id, at)
