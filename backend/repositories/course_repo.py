from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course import Course
from backend.models.lesson import Lesson
from backend.models.exercise import Exercise
from backend.models.progress import UserProgress


class CourseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(select(Course).order_by(Course.order))
        return result.scalars().all()

    async def get_by_id(self, course_id: int):
        result = await self.session.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def get_by_language(self, language_id: int):
        result = await self.session.execute(select(Course)
        .where(Course.language_id == language_id).order_by(Course.order))
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
        result = await self.session.execute(select(Lesson.id).where(Lesson.course_id == course.id))
        lesson_ids = result.scalars().all()

        if lesson_ids:
            await self.session.execute(delete(UserProgress).where(UserProgress.lesson_id.in_(lesson_ids)))
            await self.session.execute(delete(Exercise).where(Exercise.lesson_id.in_(lesson_ids)))
            await self.session.execute(delete(Lesson).where(Lesson.id.in_(lesson_ids)))

        await self.session.delete(course)
        await self.session.commit()