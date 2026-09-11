from datetime import date

from backend.models.challenge import DailyChallenge
from backend.repositories.challenge_repo import ChallengeRepository
from backend.schemas.challenge_schema import ChallengeCreate,ChallengeUpdate


class ChallengeService:
    def __init__(self,repository: ChallengeRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self,challenge_id: int):
        return await self.repository.get_by_id(challenge_id)

    async def get_today(self):
        return await self.repository.get_by_date(date.today())

    async def create(self,data: ChallengeCreate):
        existing = await self.repository.get_by_date(
            data.challenge_date
        )

        if existing:
            return None

        challenge = DailyChallenge(
            title=data.title,
            description=data.description,
            xp_reward=data.xp_reward,
            challenge_date=data.challenge_date
        )

        return await self.repository.create(challenge)

    async def update(
        self,
        challenge_id: int,
        data: ChallengeUpdate
    ):
        challenge = await self.repository.get_by_id(challenge_id)

        if not challenge:
            return None

        for key,value in data.model_dump(exclude_unset=True).items():
            setattr(challenge,key,value)

        return await self.repository.update(challenge)

    async def delete(self,challenge_id: int):
        challenge = await self.repository.get_by_id(challenge_id)

        if not challenge:
            return False

        await self.repository.delete(challenge)
        return True