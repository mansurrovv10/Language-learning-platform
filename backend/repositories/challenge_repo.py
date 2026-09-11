from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.challenge import DailyChallenge


class ChallengeRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(
            select(DailyChallenge).order_by(
                DailyChallenge.challenge_date.desc()
            )
        )
        return result.scalars().all()

    async def get_by_id(self,challenge_id: int):
        result = await self.session.execute(
            select(DailyChallenge).where(
                DailyChallenge.id == challenge_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_date(self,challenge_date: date):
        result = await self.session.execute(
            select(DailyChallenge).where(
                DailyChallenge.challenge_date == challenge_date
            )
        )
        return result.scalar_one_or_none()

    async def create(self,challenge: DailyChallenge):
        self.session.add(challenge)
        await self.session.commit()
        await self.session.refresh(challenge)
        return challenge

    async def update(self,challenge: DailyChallenge):
        await self.session.commit()
        await self.session.refresh(challenge)
        return challenge

    async def delete(self,challenge: DailyChallenge):
        await self.session.delete(challenge)
        await self.session.commit()