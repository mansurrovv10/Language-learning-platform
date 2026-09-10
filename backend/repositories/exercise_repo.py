from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.exercise import Exercise


class ExerciseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(
            select(Exercise)
        )
        return result.scalars().all()

    async def get_by_id(self, exercise_id: int):
        result = await self.session.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        return result.scalar_one_or_none()

    async def get_by_lesson(self, lesson_id: int):
        result = await self.session.execute(
            select(Exercise).where(Exercise.lesson_id == lesson_id)
        )
        return result.scalars().all()

    async def create(self, exercise: Exercise):
        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def update(self, exercise: Exercise):
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def delete(self, exercise: Exercise):
        await self.session.delete(exercise)
        await self.session.commit()