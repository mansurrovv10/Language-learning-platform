import hashlib
import json
import uuid
from datetime import datetime, timedelta

from backend.config import MAX_HEARTS
from backend.models.practice import PracticeSession, PracticeSessionItem
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.practice_repo import PracticeRepository
from backend.schemas.gamification_schema import HeartsResponse
from backend.schemas.practice_schema import (
    PracticeCompletion,
    PracticeItemResponse,
    PracticeResult,
    PracticeSessionResponse,
)
from backend.services.exercise_service import ExerciseService
from backend.time import as_utc, utc_now


class PracticeError(ValueError):
    pass


class PracticeService:
    def __init__(
        self,
        repository: PracticeRepository,
        gamification_repository: GamificationRepository,
    ):
        self.repository = repository
        self.gamification_repository = gamification_repository

    async def create_session(
        self, user_id: uuid.UUID, at: datetime | None = None
    ) -> PracticeSessionResponse:
        instant = utc_now() if at is None else as_utc(at)
        db = self.repository.session
        try:
            await self.repository.lock_user(user_id)
            active = await self.repository.get_active(user_id, instant)
            if active is not None:
                response = await self._session_response(active)
                await db.commit()
                return response
            exercises = await self.repository.get_candidates(user_id, instant)
            if not exercises:
                raise PracticeError("PRACTICE_NOT_AVAILABLE")
            practice = PracticeSession(
                user_id=user_id,
                created_at=instant,
                expires_at=instant + timedelta(minutes=15),
                heart_awarded=False,
            )
            db.add(practice)
            await db.flush()
            for position, exercise in enumerate(exercises):
                db.add(
                    PracticeSessionItem(
                        session_id=practice.id,
                        exercise_id=exercise.id,
                        position=position,
                        exercise_type=exercise.type.value,
                        question=exercise.question,
                        options=exercise.options,
                        correct_answer=exercise.correct_answer,
                    )
                )
            await db.commit()
            return await self._session_response(practice)
        except Exception:
            await db.rollback()
            raise

    async def _session_response(
        self, practice: PracticeSession
    ) -> PracticeSessionResponse:
        items = await self.repository.get_items(practice.id)
        return PracticeSessionResponse(
            id=practice.id,
            created_at=practice.created_at,
            expires_at=practice.expires_at,
            items=[
                PracticeItemResponse(
                    id=item.id,
                    exercise_id=item.exercise_id,
                    position=item.position,
                    exercise_type=item.exercise_type,
                    question=item.question,
                    options=item.options,
                )
                for item in items
            ],
        )

    async def complete_session(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        data: PracticeCompletion,
        at: datetime | None = None,
    ) -> PracticeResult:
        instant = utc_now() if at is None else as_utc(at)
        db = self.repository.session
        try:
            practice = await self.repository.lock_session(session_id, user_id)
            if practice is None:
                raise PracticeError("PRACTICE_NOT_FOUND")
            items = await self.repository.get_items(session_id)
            answers = {answer.item_id: answer.answer for answer in data.answers}
            expected_ids = {item.id for item in items}
            if len(answers) != len(data.answers) or set(answers) != expected_ids:
                raise PracticeError("PRACTICE_ANSWERS_INVALID")
            request_hash = hashlib.sha256(
                json.dumps(
                    sorted(answers.items()),
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
            if practice.completed_at is not None:
                if practice.request_hash != request_hash:
                    raise PracticeError("IDEMPOTENCY_CONFLICT")
                await db.commit()
                return PracticeResult.model_validate(practice.response)
            if instant >= practice.expires_at:
                raise PracticeError("PRACTICE_EXPIRED")

            matcher = object.__new__(ExerciseService)
            correct_count = sum(
                matcher._answers_equal(
                    item.correct_answer,
                    answers[item.id],
                    unordered_lists=item.exercise_type == "match",
                )
                for item in items
            )
            score = round(correct_count * 100 / len(items), 2)
            passed = score >= 80
            hearts = await self.gamification_repository.get_current_hearts(
                user_id, commit=False
            )
            heart_awarded = passed and hearts.hearts < MAX_HEARTS
            if heart_awarded:
                hearts.hearts += 1
                if hearts.hearts >= MAX_HEARTS:
                    hearts.last_heart_lost_at = None
                await db.flush()
            heart_status_data = (
                await self.gamification_repository.get_hearts_status(
                    user_id, commit=False
                )
            )
            result = PracticeResult(
                session_id=practice.id,
                score=score,
                passed=passed,
                heart_awarded=heart_awarded,
                hearts_left=hearts.hearts,
                heart_status=HeartsResponse(**heart_status_data),
            )
            practice.completed_at = instant
            practice.score = score
            practice.passed = passed
            practice.heart_awarded = heart_awarded
            practice.request_hash = request_hash
            practice.response = result.model_dump(mode="json")
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise
