import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.level_test import LevelTest, LevelTestAttempt, LevelTestQuestion
from backend.models.user_language import UserLanguage
from backend.models.course import Course
from backend.models.lesson import Lesson
from backend.models.progress import UserProgress


class LevelTestRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_test(self,test_id: uuid.UUID):
        result = await self.session.execute(select(LevelTest).where(LevelTest.id == test_id))
        return result.scalar_one_or_none()

    async def get_tests(self,language_id: int | None = None):
        query = select(LevelTest).order_by(LevelTest.created_at.desc())
        if language_id is not None:
            query = query.where(LevelTest.language_id == language_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_active_test(self,language_id: int,is_placement: bool,target_level=None):
        query = select(LevelTest).where(
            LevelTest.language_id == language_id,
            LevelTest.is_placement == is_placement,
            LevelTest.is_active == True)
        if target_level is not None:
            query = query.where(LevelTest.target_level == target_level)
        result = await self.session.execute(query.order_by(LevelTest.created_at.desc()))
        return result.scalars().first()

    async def create_test(self,test: LevelTest):
        self.session.add(test)
        await self.session.commit()
        await self.session.refresh(test)
        return test

    async def update_test(self,test: LevelTest):
        await self.session.commit()
        await self.session.refresh(test)
        return test

    async def delete_test(self,test: LevelTest):
        await self.session.delete(test)
        await self.session.commit()

    async def get_questions(self,test_id: uuid.UUID):
        result = await self.session.execute(select(LevelTestQuestion)
            .where(LevelTestQuestion.test_id == test_id)
            .order_by(LevelTestQuestion.order))
        return result.scalars().all()

    async def get_question(self,question_id: int):
        result = await self.session.execute(select(LevelTestQuestion).where(LevelTestQuestion.id == question_id))
        return result.scalar_one_or_none()

    async def create_question(self,question: LevelTestQuestion):
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def update_question(self,question: LevelTestQuestion):
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def delete_question(self,question: LevelTestQuestion):
        await self.session.delete(question)
        await self.session.commit()

    async def get_user_language(self,user_id: uuid.UUID,language_id: int):
        result = await self.session.execute(select(UserLanguage).where(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id))
        return result.scalar_one_or_none()

    async def create_user_language(self,user_language: UserLanguage):
        self.session.add(user_language)
        await self.session.commit()
        await self.session.refresh(user_language)
        return user_language

    async def update_user_language(self,user_language: UserLanguage):
        await self.session.commit()
        await self.session.refresh(user_language)
        return user_language

    async def create_attempt(self,attempt: LevelTestAttempt):
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def get_attempt(self,attempt_id: uuid.UUID):
        result = await self.session.execute(select(LevelTestAttempt).where(LevelTestAttempt.id == attempt_id))
        return result.scalar_one_or_none()

    async def complete_attempt(self,attempt: LevelTestAttempt,score: float,passed: bool,result_level):
        attempt.score = score
        attempt.passed = passed
        attempt.result_level = result_level
        attempt.completed_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def are_level_lessons_completed(self,user_id: uuid.UUID,language_id: int,level):
        result = await self.session.execute(select(Lesson.id)
            .join(Course,Lesson.course_id == Course.id)
            .where(Course.language_id == language_id,Course.level == level))
        lesson_ids = result.scalars().all()
        if not lesson_ids:
            return False
        result = await self.session.execute(select(UserProgress.lesson_id).where(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id.in_(lesson_ids),
            UserProgress.completed == True))
        completed_ids = set(result.scalars().all())
        return set(lesson_ids).issubset(completed_ids)
