import uuid

from backend.repositories.leaderboard_repo import LeaderboardRepository


class LeaderboardService:
    def __init__(self,repository: LeaderboardRepository):
        self.repository = repository

    async def get_leaderboard(self,limit: int = 10):
        return await self.repository.get_top(limit)

    async def get_user(self,user_id: uuid.UUID):
        entry = await self.repository.get_user(user_id)
        total = await self.repository.get_user_total_xp(user_id)
        rank = await self.repository.get_user_rank(user_id)

        if entry is None:
            entry = await self.repository.upsert_user(user_id)

        return {
            "user_id": user_id,
            "xp": total,
            "rank": rank if rank is not None else entry.rank
        }

    async def refresh(self):
        count = await self.repository.recompute_all()
        return {"recomputed": count}