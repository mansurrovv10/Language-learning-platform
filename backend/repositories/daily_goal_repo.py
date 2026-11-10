import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.daily_goal import UserDailyGoal
from backend.models.gamification import XPHistory
from backend.time import utc_now


class DailyGoalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: uuid.UUID) -> UserDailyGoal:
        await self.session.execute(
            pg_insert(UserDailyGoal)
            .values(user_id=user_id, target_xp=20, updated_at=utc_now())
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        await self.session.commit()
        return await self.session.scalar(
            select(UserDailyGoal).where(UserDailyGoal.user_id == user_id)
        )

    async def set_target(
        self, user_id: uuid.UUID, target_xp: int
    ) -> UserDailyGoal:
        statement = (
            pg_insert(UserDailyGoal)
            .values(user_id=user_id, target_xp=target_xp, updated_at=utc_now())
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={"target_xp": target_xp, "updated_at": utc_now()},
            )
            .returning(UserDailyGoal)
        )
        goal = (await self.session.execute(statement)).scalar_one()
        await self.session.commit()
        return goal

    async def sum_xp(
        self, user_id: uuid.UUID, start_at: datetime, end_at: datetime
    ) -> int:
        total = await self.session.scalar(
            select(func.coalesce(func.sum(XPHistory.xp), 0)).where(
                XPHistory.user_id == user_id,
                XPHistory.created_at >= start_at,
                XPHistory.created_at < end_at,
            )
        )
        return int(total or 0)
