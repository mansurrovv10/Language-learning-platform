from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course import Course


class CourseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(
            select(Course).order_by(Course.order)
        )
        return result.scalars().all()

    async def get_by_id(self, course_id: int):
        result = await self.session.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    async def get_by_language(self, language_id: int):
        result = await self.session.execute(
            select(Course)
            .where(Course.language_id == language_id)
            .order_by(Course.order)
        )
        return result.scalars().all()

    async def create(self, course: Course):
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return course

    async def update(self, course: Course):
        await self.session.commit()
        await self.session.refresh(course)
        return course

    async def delete(self, course: Course):
        await self.session.delete(course)
        await self.session.commit()