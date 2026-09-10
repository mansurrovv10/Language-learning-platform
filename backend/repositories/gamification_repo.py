import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.gamification import XPHistory, Streak


class GamificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_xp_history(self, user_id: uuid.UUID):
        result = await self.session.execute(
            select(XPHistory)
            .where(XPHistory.user_id == user_id)
            .order_by(XPHistory.created_at.desc())
        )
        return result.scalars().all()

    async def add_xp(self, data):
        xp = XPHistory(
            user_id=data.user_id,
            xp=data.xp,
            reason=data.reason
        )
        self.session.add(xp)
        await self.session.commit()
        await self.session.refresh(xp)
        return xp

    async def get_streak(self, user_id: uuid.UUID):
        result = await self.session.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_streak(self, user_id: uuid.UUID):
        streak = Streak(
            user_id=user_id,
            current_streak=0
        )
        self.session.add(streak)
        await self.session.commit()
        await self.session.refresh(streak)
        return streak

    async def update_streak(self, streak):
        self.session.add(streak)
        await self.session.commit()
        await self.session.refresh(streak)
        return streak