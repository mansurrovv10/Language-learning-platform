import uuid
from datetime import date,timedelta

from backend.models.exercise import Exercise
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.achievement_repo import AchievementRepository
from backend.schemas.exercise_schema import ExerciseCreate,ExerciseUpdate,ExerciseResult,ExerciseSubmit
from backend.services.achievement_service import AchievementService


class ExerciseService:
    def __init__(
        self,
        repository: ExerciseRepository,
        progress_repository: ProgressRepository,
        gamification_repository: GamificationRepository,
        achievement_repository: AchievementRepository
    ):
        self.repository = repository
        self.progress_repository = progress_repository
        self.gamification_repository = gamification_repository
        self.achievement_service = AchievementService(
            achievement_repository,
            gamification_repository
        )

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self,exercise_id: int):
        return await self.repository.get_by_id(exercise_id)

    async def get_by_lesson(self,lesson_id: int):
        return await self.repository.get_by_lesson(lesson_id)

    async def create(self,data: ExerciseCreate):
        exercise = Exercise(**data.model_dump())
        return await self.repository.create(exercise)

    async def update(self,exercise_id: int,data: ExerciseUpdate):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return None

        for key,value in data.model_dump(exclude_unset=True).items():
            setattr(exercise,key,value)

        return await self.repository.update(exercise)

    async def delete(self,exercise_id: int):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return False

        await self.repository.delete(exercise)
        return True

    async def submit_exercise(
        self,
        exercise_id: int,
        data: ExerciseSubmit,
        user_id: uuid.UUID
    ):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return None

        correct = self._check_answer(exercise,data.answer)
        score = 10 if correct else 0

        progress = await self.progress_repository.get_by_user_and_lesson(
            user_id,
            exercise.lesson_id
        )

        already_completed = progress.completed if progress else False

        if progress:
            if correct and score > progress.score:
                await self.progress_repository.update(
                    progress.id,
                    completed=True,
                    score=score
                )
        else:
            await self.progress_repository.create(
                user_id=user_id,
                lesson_id=exercise.lesson_id,
                completed=correct,
                score=score
            )

        if correct and not already_completed:
            await self.gamification_repository.add_xp(
                user_id=user_id,
                xp=10,
                reason="exercise_completed"
            )

            await self._update_streak(user_id)
            await self._check_exercise_achievements(user_id)

        return ExerciseResult(
            correct=correct,
            score=score
        )

    async def _check_exercise_achievements(self,user_id: uuid.UUID):
        xp_history = await self.gamification_repository.get_xp_history(
            user_id
        )

        exercise_count = sum(
            1
            for item in xp_history
            if item.reason == "exercise_completed"
        )

        await self.achievement_service.check_achievements(
            user_id,
            "exercises",
            exercise_count
        )

    async def _update_streak(self,user_id: uuid.UUID):
        streak = await self.gamification_repository.get_streak(user_id)

        if not streak:
            streak = await self.gamification_repository.create_streak(user_id)

        today = date.today()

        if streak.last_activity == today:
            return

        if streak.last_activity == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        streak.last_activity = today

        await self.gamification_repository.update_streak(streak)

    def _normalize(self,value):
        if isinstance(value,str):
            return value.strip().lower()

        if isinstance(value,dict):
            return {
                self._normalize(key): self._normalize(item)
                for key,item in value.items()
            }

        if isinstance(value,list):
            return [
                self._normalize(item)
                for item in value
            ]

        return value

    def _check_answer(self,exercise: Exercise,answer):
        expected = self._normalize(exercise.correct_answer)
        actual = self._normalize(answer)

        return actual == expected