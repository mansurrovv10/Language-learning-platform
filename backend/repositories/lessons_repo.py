from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.lesson import Lesson


class LessonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(select(Lesson))
        return result.scalars().all()

    async def get_by_id(self, lesson_id: int):
        result = await self.session.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        return result.scalar_one_or_none()

    async def get_by_course(self, course_id: int):
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.order)
        )
        return result.scalars().all()

    async def create(self, data):
        lesson = Lesson(
            course_id=data.course_id,
            title=data.title,
            order=data.order,
            is_locked=data.is_locked
        )
        self.session.add(lesson)
        await self.session.commit()
        await self.session.refresh(lesson)
        return lesson

    async def update(self, lesson_id: int, data):
        lesson = await self.get_by_id(lesson_id)

        if not lesson:
            return None

        if data.course_id is not None:
            lesson.course_id = data.course_id

        if data.title is not None:
            lesson.title = data.title

        if data.order is not None:
            lesson.order = data.order

        if data.is_locked is not None:
            lesson.is_locked = data.is_locked

        await self.session.commit()
        await self.session.refresh(lesson)
        return lesson

    async def delete(self, lesson_id: int):
        lesson = await self.get_by_id(lesson_id)

        if not lesson:
            return False

        await self.session.delete(lesson)
        await self.session.commit()
        return True