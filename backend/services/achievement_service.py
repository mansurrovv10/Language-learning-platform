import uuid

from backend.models.achievement import Achievement
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.schemas.achievement_schema import AchievementCreate,AchievementUpdate


class AchievementService:
    def __init__(
        self,
        repository: AchievementRepository,
        gamification_repository: GamificationRepository
    ):
        self.repository = repository
        self.gamification_repository = gamification_repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self,achievement_id: int):
        return await self.repository.get_by_id(achievement_id)

    async def create(self,data: AchievementCreate):
        achievement = Achievement(
            title=data.title,
            description=data.description,
            xp_reward=data.xp_reward,
            conditions=data.conditions
        )
        return await self.repository.create(achievement)

    async def update(
        self,
        achievement_id: int,
        data: AchievementUpdate
    ):
        achievement = await self.repository.get_by_id(achievement_id)

        if not achievement:
            return None

        for key,value in data.model_dump(exclude_unset=True).items():
            setattr(achievement,key,value)

        return await self.repository.update(achievement)

    async def delete(self,achievement_id: int):
        achievement = await self.repository.get_by_id(achievement_id)

        if not achievement:
            return False

        await self.repository.delete(achievement)
        return True

    async def get_user_achievements(self,user_id: uuid.UUID):
        return await self.repository.get_user_achievements(user_id)

    async def check_achievements(
        self,
        user_id: uuid.UUID,
        category: str,
        count: int
    ):
        achievements = await self.repository.get_all()
        awarded = []

        for achievement in achievements:
            conditions = achievement.conditions

            if not isinstance(conditions, dict):
                continue

            if conditions.get("type") != category:
                continue

            if count < conditions.get("count", 0):
                continue

            user_achievement = await self.check_and_award(
                user_id,
                achievement.id
            )

            if user_achievement:
                awarded.append(user_achievement)

        return awarded

    async def check_and_award(
        self,
        user_id: uuid.UUID,
        achievement_id: int
    ):
        achievement = await self.repository.get_by_id(achievement_id)

        if not achievement:
            return None

        existing = await self.repository.get_user_achievement(
            user_id,
            achievement_id
        )

        if existing:
            return existing

        user_achievement = await self.repository.create_user_achievement(
            user_id,
            achievement_id
        )

        if achievement.xp_reward > 0:
            await self.gamification_repository.add_xp(
                user_id=user_id,
                xp=achievement.xp_reward,
                reason=f"achievement:{achievement.title}"
            )

        return user_achievement