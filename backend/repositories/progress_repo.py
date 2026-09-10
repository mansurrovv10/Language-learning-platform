import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.progress import UserProgress


class ProgressRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(select(UserProgress))
        return result.scalars().all()

    async def get_by_id(self, progress_id: int):
        result = await self.session.execute(
            select(UserProgress).where(UserProgress.id == progress_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID):
        result = await self.session.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_lesson(self, lesson_id: int):
        result = await self.session.execute(
            select(UserProgress).where(UserProgress.lesson_id == lesson_id)
        )
        return result.scalars().all()

    async def create(self, data):
        progress = UserProgress(
            user_id=data.user_id,
            lesson_id=data.lesson_id,
            completed=data.completed,
            score=data.score
        )
        self.session.add(progress)
        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def update(self, progress_id: int, data):
        progress = await self.get_by_id(progress_id)

        if not progress:
            return None

        if data.completed is not None:
            progress.completed = data.completed
            if data.completed:
                progress.completed_at = datetime.utcnow()

        if data.score is not None:
            progress.score = data.score

        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def delete(self, progress_id: int):
        progress = await self.get_by_id(progress_id)

        if not progress:
            return False

        await self.session.delete(progress)
        await self.session.commit()
        return True