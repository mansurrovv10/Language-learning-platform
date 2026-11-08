import uuid
from datetime import datetime,timedelta
from backend.repositories.gamification_repo import GamificationRepository
from backend.time import bishkek_date


class GamificationService:
    def __init__(self,repository: GamificationRepository):
        self.repository = repository

    async def get_xp_history(self,user_id: uuid.UUID):
        return await self.repository.get_xp_history(user_id)

    async def add_xp(self,user_id: uuid.UUID,xp: int,reason: str):
        return await self.repository.add_xp(user_id,xp,reason)

    async def get_streak(self,user_id: uuid.UUID):
        return await self.repository.get_streak(user_id)

    async def get_hearts_status(self,user_id: uuid.UUID):
        return await self.repository.get_hearts_status(user_id)

    async def advance_streak_for_learning(
        self,
        user_id: uuid.UUID,
        occurred_at: datetime,
        commit: bool = True,
    ):
        streak = await self.repository.get_streak(user_id)

        if not streak:
            streak = await self.repository.create_streak(user_id,commit=commit)

        today = bishkek_date(occurred_at)

        if streak.last_activity == today:
            return streak

        if streak.last_activity == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        streak.last_activity = today

        return await self.repository.update_streak(streak,commit=commit)
