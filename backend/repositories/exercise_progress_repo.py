import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.exercise import Exercise
from backend.models.exercise_progress import UserExerciseProgress


class ExerciseProgressRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_by_user_and_exercise(self,user_id: uuid.UUID,exercise_id: int):
        result = await self.session.execute(select(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user_id,
            UserExerciseProgress.exercise_id == exercise_id))
        return result.scalar_one_or_none()

    async def save_result(self,user_id: uuid.UUID,exercise_id: int,completed: bool,score: int):
        progress = await self.get_by_user_and_exercise(user_id,exercise_id)
        if not progress:
            progress = UserExerciseProgress(user_id=user_id,exercise_id=exercise_id,
                completed=completed,score=score)
            self.session.add(progress)
        elif completed and score > progress.score:
            progress.completed = True
            progress.score = score
        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def are_lesson_exercises_completed(self,user_id: uuid.UUID,lesson_id: int):
        result = await self.session.execute(select(Exercise.id).where(Exercise.lesson_id == lesson_id))
        exercise_ids = result.scalars().all()
        if not exercise_ids:
            return False
        result = await self.session.execute(select(UserExerciseProgress.exercise_id).where(
            UserExerciseProgress.user_id == user_id,
            UserExerciseProgress.exercise_id.in_(exercise_ids),
            UserExerciseProgress.completed == True))
        return set(exercise_ids).issubset(set(result.scalars().all()))
