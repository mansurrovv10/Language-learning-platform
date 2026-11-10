import hashlib
import json
import re
import unicodedata
import uuid

from backend.config import MAX_HEARTS
from backend.models.exercise import Exercise, ExerciseType
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.exercise_submission_repo import ExerciseSubmissionRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.schemas.exercise_schema import (
    ExerciseCreate,
    ExerciseResult,
    ExerciseSubmit,
    ExerciseUpdate,
)
from backend.schemas.gamification_schema import HeartsResponse
from backend.services.achievement_service import AchievementService
from backend.services.gamification_service import GamificationService
from backend.services.review_service import ReviewService
from backend.time import utc_now


class NotEnoughHeartsError(Exception):
    def __init__(self,seconds_to_next_heart: int):
        super().__init__("Not enough hearts")
        self.seconds_to_next_heart = seconds_to_next_heart


MAX_IDEMPOTENCY_KEY_LENGTH = 255


class ExerciseService:
    ANSWER_ENVELOPE_KEYS = ("answer","value","correct_answer","correct","option",
                           "text","label","key","id","index")

    def __init__(
        self,
        repository: ExerciseRepository,
        progress_repository: ProgressRepository,
        exercise_progress_repository: ExerciseProgressRepository,
        gamification_repository: GamificationRepository,
        achievement_repository: AchievementRepository,
        submission_repository: ExerciseSubmissionRepository | None = None,
        review_service: ReviewService | None = None):
        self.repository = repository
        self.progress_repository = progress_repository
        self.exercise_progress_repository = exercise_progress_repository
        self.gamification_repository = gamification_repository
        self.submission_repository = submission_repository
        self.review_service = review_service
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
        user_id: uuid.UUID,
        idempotency_key: str | None = None,
        is_admin: bool = False):
        if is_admin:
            exercise = await self.repository.get_by_id(exercise_id)
            if not exercise:
                return None
            correct = self._check_answer(exercise,data.answer)
            return ExerciseResult(
                correct=correct,
                score=10 if correct else 0,
                hearts_left=MAX_HEARTS,
                heart_status=None,
            )

        if self.submission_repository is not None:
            if not idempotency_key or not idempotency_key.strip():
                raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
            if len(idempotency_key.strip()) > MAX_IDEMPOTENCY_KEY_LENGTH:
                raise ValueError("IDEMPOTENCY_KEY_TOO_LONG")
            return await self._submit_atomic(
                exercise_id,data,user_id,idempotency_key.strip())

        return await self._submit_legacy(exercise_id,data,user_id)

    async def _submit_legacy(
        self,exercise_id: int,data: ExerciseSubmit,user_id: uuid.UUID):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return None

        hearts = await self.gamification_repository.get_current_hearts(user_id)

        exercise_progress = await self.exercise_progress_repository.get_by_user_and_exercise(
            user_id,exercise.id)
        already_exercise_completed = exercise_progress.completed if exercise_progress else False

        # Жүрөкчө 0 болсо: жаңы exercise бөгөттөлөт,
        # мурун аткарылган exercise (practice) жана админ үчүн бөгөттөлбөйт.
        if hearts.hearts <= 0 and not already_exercise_completed:
            raise NotEnoughHeartsError(
                self.gamification_repository.seconds_to_next_heart(hearts))

        correct = self._check_answer(exercise,data.answer)
        score = 10 if correct else 0

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

            await GamificationService(
                self.gamification_repository
            ).advance_streak_for_learning(user_id,utc_now())
            await self._check_exercise_achievements(user_id)

        return ExerciseResult(
            correct=correct,
            score=score,
            hearts_left=hearts_left
        )

    async def _submit_atomic(
        self,exercise_id: int,data: ExerciseSubmit,user_id: uuid.UUID,
        idempotency_key: str):
        request_hash = hashlib.sha256(json.dumps(
            {"exercise_id":exercise_id,"answer":data.answer},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",",":"),
            allow_nan=False,
        ).encode("utf-8")).hexdigest()

        session = self.repository.session
        try:
            exercise = await self.repository.get_by_id(exercise_id)
            if not exercise:
                await session.rollback()
                return None

            submission,replayed = await self.submission_repository.get_or_reserve(
                user_id,idempotency_key,exercise_id,request_hash)
            if replayed:
                result = ExerciseResult.model_validate(submission.response)
                await session.commit()
                return result

            hearts = await self.gamification_repository.get_current_hearts(
                user_id,commit=False)
            exercise_progress = (
                await self.exercise_progress_repository.get_by_user_and_exercise(
                    user_id,exercise.id)
            )
            already_completed = bool(exercise_progress and exercise_progress.completed)

            if hearts.hearts <= 0 and not already_completed:
                raise NotEnoughHeartsError(
                    self.gamification_repository.seconds_to_next_heart(hearts))

            correct = self._check_answer(exercise,data.answer)
            score = 10 if correct else 0
            if self.review_service is not None:
                await self.review_service.record_result(
                    user_id, exercise.id, correct, at=utc_now(), commit=False
                )
            if not correct and not already_completed:
                hearts_left = await self.gamification_repository.lose_heart(
                    user_id,commit=False)
            else:
                hearts_left = hearts.hearts

            await self.exercise_progress_repository.save_result(
                user_id,exercise.id,correct,score,commit=False)
            progress = await self.progress_repository.get_by_user_and_lesson(
                user_id,exercise.lesson_id)
            lesson_completed = (
                await self.exercise_progress_repository.are_lesson_exercises_completed(
                    user_id,exercise.lesson_id)
            )
            if progress:
                if lesson_completed and not progress.completed:
                    await self.progress_repository.update(
                        progress.id,completed=True,score=100,commit=False)
            else:
                await self.progress_repository.create(
                    user_id=user_id,
                    lesson_id=exercise.lesson_id,
                    completed=lesson_completed,
                    score=100 if lesson_completed else 0,
                    commit=False,
                )

            if correct and not already_completed:
                await self.gamification_repository.add_xp(
                    user_id=user_id,
                    xp=10,
                    reason="exercise_completed",
                    commit=False,
                )
                await GamificationService(
                    self.gamification_repository
                ).advance_streak_for_learning(user_id,utc_now(),commit=False)
                await self._check_exercise_achievements(user_id,commit=False)

            heart_status = await self.gamification_repository.get_hearts_status(
                user_id,commit=False)
            result = ExerciseResult(
                correct=correct,
                score=score,
                hearts_left=hearts_left,
                heart_status=HeartsResponse(**heart_status),
            )
            await self.submission_repository.store_response(
                submission,result.model_dump(mode="json"))
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        return result

    async def _check_exercise_achievements(
        self,user_id: uuid.UUID,commit: bool = True):
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
            exercise_count,
            commit=commit,
        )

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

    def _answers_equal(self,expected,actual,unordered_lists: bool = False):
        expected = self._as_pairs(self._normalize(self._unwrap(expected)))
        actual = self._as_pairs(self._normalize(self._unwrap(actual)))

        return self._values_equal(expected,actual,unordered_lists)

    def _values_equal(self,expected,actual,unordered_lists: bool = False):
        if expected == actual:
            return True

        if isinstance(expected,list) and isinstance(actual,list):
            if unordered_lists:
                return self._collections_equal(expected,actual)
            if len(expected) != len(actual):
                return False
            return all(
                self._values_equal(expected_item,actual_item)
                for expected_item,actual_item in zip(expected,actual)
            )

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
        if exercise.correct_answer is None or answer is None:
            return False
        return self._answers_equal(
            exercise.correct_answer,
            answer,
            unordered_lists=exercise.type == ExerciseType.MATCH,
        )
