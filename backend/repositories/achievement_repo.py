import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.achievement import Achievement,UserAchievement


class AchievementRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(
            select(Achievement)
        )
        return result.scalars().all()

    async def get_by_id(self,achievement_id: int):
        result = await self.session.execute(
            select(Achievement).where(
                Achievement.id == achievement_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self,achievement: Achievement):
        self.session.add(achievement)
        await self.session.commit()
        await self.session.refresh(achievement)
        return achievement

    async def update(self,achievement: Achievement):
        await self.session.commit()
        await self.session.refresh(achievement)
        return achievement

    async def delete(self,achievement: Achievement):
        await self.session.delete(achievement)
        await self.session.commit()

    async def get_user_achievements(self,user_id: uuid.UUID):
        result = await self.session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id
            )
        )
        return result.scalars().all()

    async def get_user_achievement(
        self,
        user_id: uuid.UUID,
        achievement_id: int
    ):
        result = await self.session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id
            )
        )
        return result.scalar_one_or_none()

    async def create_user_achievement(
        self,
        user_id: uuid.UUID,
        achievement_id: int
    ):
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id
        )

        self.session.add(user_achievement)
        await self.session.commit()
        await self.session.refresh(user_achievement)

        return user_achievement