import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course import Course
from backend.models.lesson import Lesson
from backend.models.user_language import UserLanguage


class LearningPathRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_user_language(self,user_id: uuid.UUID,language_id: int):
        result = await self.session.execute(select(UserLanguage).where(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id))
        return result.scalar_one_or_none()

    async def get_courses(self,language_id: int):
        result = await self.session.execute(select(Course)
            .where(Course.language_id == language_id)
            .order_by(Course.level,Course.order))
        return result.scalars().all()

    async def get_lessons(self,course_id: int):
        result = await self.session.execute(select(Lesson)
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.order))
        return result.scalars().all()

    async def get_course(self,course_id: int):
        result = await self.session.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def get_course_by_lesson(self,lesson_id: int):
        result = await self.session.execute(select(Course)
            .join(Lesson,Lesson.course_id == Course.id)
            .where(Lesson.id == lesson_id))
        return result.scalar_one_or_none()
