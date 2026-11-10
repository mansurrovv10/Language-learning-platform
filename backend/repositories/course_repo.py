from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course import Course
from backend.models.exercise import Exercise
from backend.models.exercise_progress import UserExerciseProgress
from backend.models.lesson import Lesson
from backend.models.progress import UserProgress
from backend.pagination import normalize_page


class CourseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(select(Course).order_by(Course.order))
        return result.scalars().all()

    async def get_paged(self, q=None, limit=20, offset=0):
        q, limit, offset = normalize_page(q, limit, offset)
        filters = []
        if q:
            pattern = f"%{q}%"
            filters.append(or_(Course.title.ilike(pattern), Course.description.ilike(pattern)))
        total = int(await self.session.scalar(
            select(func.count()).select_from(Course).where(*filters)) or 0)
        items = list(await self.session.scalars(
            select(Course).where(*filters)
            .order_by(Course.language_id, Course.order, Course.id)
            .limit(limit).offset(offset)))
        return items, total

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
        result = await self.session.execute(
            select(Lesson.id).where(Lesson.course_id == course.id)
        )
        lesson_ids = result.scalars().all()

        if lesson_ids:
            await self.session.execute(
                delete(UserProgress).where(
                    UserProgress.lesson_id.in_(lesson_ids)
                )
            )

            result = await self.session.execute(
                select(Exercise.id).where(
                    Exercise.lesson_id.in_(lesson_ids)
                )
            )
            exercise_ids = result.scalars().all()

            if exercise_ids:
                await self.session.execute(
                    delete(UserExerciseProgress).where(
                        UserExerciseProgress.exercise_id.in_(exercise_ids)
                    )
                )

                await self.session.execute(
                    delete(Exercise).where(
                        Exercise.id.in_(exercise_ids)
                    )
                )

            await self.session.execute(
                delete(Lesson).where(
                    Lesson.id.in_(lesson_ids)
                )
            )

        await self.session.delete(course)
        await self.session.commit()
