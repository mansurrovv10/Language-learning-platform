import uuid
from datetime import date, timedelta

from backend.repositories.gamification import GamificationRepository


class GamificationService:
    def __init__(self, repository: GamificationRepository):
        self.repository = repository

    async def get_xp_history(self, user_id: uuid.UUID):
        return await self.repository.get_xp_history(user_id)

    async def add_xp(self, data):
        return await self.repository.add_xp(data)

    async def get_streak(self, user_id: uuid.UUID):
        return await self.repository.get_streak(user_id)

    async def update_streak(self, user_id: uuid.UUID):
        streak = await self.repository.get_streak(user_id)

        if not streak:
            streak = await self.repository.create_streak(user_id)

        today = date.today()

        if streak.last_activity == today:
            return streak

        if streak.last_activity == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        streak.last_activity = today

        return await self.repository.update_streak(streak)