import re
import unicodedata
import uuid
from datetime import date,timedelta

from backend.models.exercise import Exercise
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.schemas.exercise_schema import ExerciseCreate,ExerciseUpdate,ExerciseResult,ExerciseSubmit
from backend.services.achievement_service import AchievementService


class NotEnoughHeartsError(Exception):
    def __init__(self,seconds_to_next_heart: int):
        super().__init__("Not enough hearts")
        self.seconds_to_next_heart = seconds_to_next_heart


class ExerciseService:
    ANSWER_ENVELOPE_KEYS = ("answer","value","correct_answer","correct","option",
                           "text","label","key","id","index")

    def __init__(
        self,
        repository: ExerciseRepository,
        progress_repository: ProgressRepository,
        exercise_progress_repository: ExerciseProgressRepository,
        gamification_repository: GamificationRepository,
        achievement_repository: AchievementRepository):
        self.repository = repository
        self.progress_repository = progress_repository
        self.exercise_progress_repository = exercise_progress_repository
        self.gamification_repository = gamification_repository
        self.achievement_service = AchievementService(
            achievement_repository,
            gamification_repository)

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
        user_id: uuid.UUID):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return None

        hearts = await self.gamification_repository.get_current_hearts(user_id)

        if hearts.hearts <= 0:
            raise NotEnoughHeartsError(
                self.gamification_repository.seconds_to_next_heart(hearts))

        correct = self._check_answer(exercise,data.answer)
        score = 10 if correct else 0

        exercise_progress = await self.exercise_progress_repository.get_by_user_and_exercise(
            user_id,exercise.id)
        already_exercise_completed = exercise_progress.completed if exercise_progress else False

        if not correct and not already_exercise_completed:
            hearts_left = await self.gamification_repository.lose_heart(user_id)
        else:
            hearts_left = hearts.hearts

        await self.exercise_progress_repository.save_result(user_id,exercise.id,correct,score)
        progress = await self.progress_repository.get_by_user_and_lesson(user_id,exercise.lesson_id)
        lesson_completed = await self.exercise_progress_repository.are_lesson_exercises_completed(
            user_id,exercise.lesson_id)

        if progress:
            if lesson_completed and not progress.completed:
                await self.progress_repository.update(progress.id,completed=True,score=100)
        else:
            await self.progress_repository.create(user_id=user_id,lesson_id=exercise.lesson_id,
                completed=lesson_completed,score=100 if lesson_completed else 0)

        if correct and not already_exercise_completed:
            await self.gamification_repository.add_xp(
                user_id=user_id,
                xp=10,
                reason="exercise_completed"
            )

            await self._update_streak(user_id)
            await self._check_exercise_achievements(user_id)

        return ExerciseResult(
            correct=correct,
            score=score,
            hearts_left=hearts_left
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
        if isinstance(value,bool):
            return value

        if isinstance(value,(int,float)):
            return self._canonical_number(value)

        if isinstance(value,str):
            return self._normalize_text(value)

        if isinstance(value,dict):
            return {
                self._normalize(key):self._normalize(item)
                for key,item in value.items()
            }

        if isinstance(value,(list,tuple)):
            return [
                self._normalize(item)
                for item in value
            ]

        return value

    def _normalize_text(self,value: str):
        folded = re.sub(r"\s+"," ",unicodedata.normalize("NFKC",value).casefold()).strip()
        number = self._canonical_number(folded)

        return number if number is not None else folded

    def _canonical_number(self,value):
        if isinstance(value,bool):
            return None

        try:
            number = float(value)
        except (TypeError,ValueError):
            return None

        if not number == number or number in (float("inf"),float("-inf")):
            return None

        return int(number) if number.is_integer() else round(number,6)

    def _unwrap(self,value):
        if not isinstance(value,dict) or len(value) != 1:
            return value

        key = next((item for item in self.ANSWER_ENVELOPE_KEYS
            if item in value or str(item).casefold() in value),None)

        return value[key] if key is not None else value

    def _as_pairs(self,value):
        if not isinstance(value,list) or not value:
            return value

        if all(isinstance(item,(list,tuple)) and len(item) == 2 for item in value):
            return dict(value)

        return value

    def _answers_equal(self,expected,actual):
        expected = self._as_pairs(self._normalize(self._unwrap(expected)))
        actual = self._as_pairs(self._normalize(self._unwrap(actual)))

        return self._values_equal(expected,actual)

    def _values_equal(self,expected,actual):
        if expected == actual:
            return True

        if isinstance(expected,list) and isinstance(actual,list):
            return self._collections_equal(expected,actual)

        if isinstance(expected,dict) and isinstance(actual,dict):
            if expected.keys() != actual.keys():
                return False

            return all(self._values_equal(expected[key],actual[key]) for key in expected)

        return False

    def _collections_equal(self,expected,actual):
        if len(expected) != len(actual):
            return False

        remaining = list(actual)

        for item in expected:
            index = next((position for position,other in enumerate(remaining)
                if self._values_equal(item,other)),None)

            if index is None:
                return False

            remaining.pop(index)

        return True

    def _check_answer(self,exercise: Exercise,answer):
        return self._answers_equal(exercise.correct_answer,answer)
