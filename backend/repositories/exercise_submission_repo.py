import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.exercise_submission import ExerciseSubmission


class IdempotencyConflictError(ValueError):
    def __init__(self):
        super().__init__("IDEMPOTENCY_CONFLICT")


class ExerciseSubmissionRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_or_reserve(
        self,
        user_id: uuid.UUID,
        key: str,
        exercise_id: int,
        request_hash: str,
    ) -> tuple[ExerciseSubmission,bool]:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key":f"{user_id}:{key}"},
        )
        result = await self.session.execute(
            select(ExerciseSubmission).where(
                ExerciseSubmission.user_id == user_id,
                ExerciseSubmission.idempotency_key == key,
            )
        )
        submission = result.scalar_one_or_none()
        if submission:
            if submission.exercise_id != exercise_id or submission.request_hash != request_hash:
                raise IdempotencyConflictError()
            return submission,True

        submission = ExerciseSubmission(
            user_id=user_id,
            exercise_id=exercise_id,
            idempotency_key=key,
            request_hash=request_hash,
        )
        self.session.add(submission)
        await self.session.flush()
        return submission,False

    async def store_response(self,submission: ExerciseSubmission,response: dict):
        submission.response = response
        await self.session.flush()
        return submission
