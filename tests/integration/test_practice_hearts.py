import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from backend.models.course import Course, LevelChoices
from backend.models.exercise import Exercise, ExerciseType
from backend.models.gamification import Hearts, Streak, XPHistory
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.services.auth_ser import AuthService

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def _seed_practice(session, exercise_count=3):
    from backend.repositories.review_repo import ReviewRepository
    from backend.services.review_service import ReviewService

    user = await AuthService(session).register(
        f"practice-{uuid.uuid4().hex}@example.com",
        f"practice_{uuid.uuid4().hex}",
        "password123",
    )
    language = Language(
        code=f"p-{uuid.uuid4().hex[:6]}",
        name=f"Practice {uuid.uuid4().hex}",
        is_active=True,
    )
    session.add(language)
    await session.flush()
    course = Course(
        language_id=language.id,
        title="Practice",
        description="Practice",
        level=LevelChoices.A1,
        order=1,
    )
    session.add(course)
    await session.flush()
    lesson = Lesson(course_id=course.id, title="Practice", order=1)
    session.add(lesson)
    await session.flush()
    exercises = [
        Exercise(
            lesson_id=lesson.id,
            type=ExerciseType.CHOICE,
            question=f"Snapshot {index}",
            options={"items": ["yes", "no"]},
            correct_answer="yes",
        )
        for index in range(exercise_count)
    ]
    session.add_all(exercises)
    await session.commit()
    review = ReviewService(ReviewRepository(session))
    at = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    for exercise in exercises:
        await review.record_result(user.id, exercise.id, False, at, commit=True)
    return user, exercises


async def test_practice_awards_one_heart_once_without_xp_or_streak(db_session):
    """Catches replay granting hearts twice or practice mutating XP/streak."""
    from backend.repositories.gamification_repo import GamificationRepository
    from backend.repositories.practice_repo import PracticeRepository
    from backend.schemas.practice_schema import PracticeAnswer, PracticeCompletion
    from backend.services.practice_service import PracticeService

    user, exercises = await _seed_practice(db_session)
    hearts = await db_session.scalar(select(Hearts).where(Hearts.user_id == user.id))
    hearts.hearts = 4
    await db_session.commit()
    service = PracticeService(
        PracticeRepository(db_session), GamificationRepository(db_session)
    )
    session = await service.create_session(
        user.id, at=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    )
    assert len(session.items) == 3
    assert all(not hasattr(item, "correct_answer") for item in session.items)
    reused = await service.create_session(
        user.id, at=datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc)
    )
    assert reused.id == session.id
    assert db_session.in_transaction() is False

    exercises[0].question = "Changed by admin"
    exercises[0].correct_answer = "no"
    await db_session.commit()

    payload = PracticeCompletion(
        answers=[
            PracticeAnswer(item_id=item.id, answer="yes") for item in session.items
        ]
    )
    first = await service.complete_session(
        user.id,
        session.id,
        payload,
        at=datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc),
    )
    replay = await service.complete_session(
        user.id,
        session.id,
        payload,
        at=datetime(2026, 1, 1, 13, tzinfo=timezone.utc),
    )
    await db_session.refresh(hearts)

    assert first == replay
    assert first.score == 100
    assert first.passed is True
    assert first.heart_awarded is True
    assert hearts.hearts == 5
    assert await db_session.scalar(
        select(func.count()).select_from(XPHistory).where(XPHistory.user_id == user.id)
    ) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(Streak).where(Streak.user_id == user.id)
    ) == 0


async def test_practice_rejects_changed_replay_expiry_and_wrong_owner(db_session):
    """Catches changed replay, expired completion, or cross-user access."""
    from backend.repositories.gamification_repo import GamificationRepository
    from backend.repositories.practice_repo import PracticeRepository
    from backend.schemas.practice_schema import PracticeAnswer, PracticeCompletion
    from backend.services.practice_service import PracticeError, PracticeService

    owner, _ = await _seed_practice(db_session, exercise_count=1)
    owner_id = owner.id
    outsider = await AuthService(db_session).register(
        f"outsider-{uuid.uuid4().hex}@example.com",
        f"outsider_{uuid.uuid4().hex}",
        "password123",
    )
    outsider_id = outsider.id
    service = PracticeService(
        PracticeRepository(db_session), GamificationRepository(db_session)
    )
    with pytest.raises(PracticeError, match="PRACTICE_NOT_AVAILABLE"):
        await service.create_session(outsider_id)
    session = await service.create_session(
        owner_id, at=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    )
    correct = PracticeCompletion(
        answers=[PracticeAnswer(item_id=session.items[0].id, answer="yes")]
    )
    await service.complete_session(
        owner_id,
        session.id,
        correct,
        at=datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc),
    )
    changed = PracticeCompletion(
        answers=[PracticeAnswer(item_id=session.items[0].id, answer="no")]
    )
    with pytest.raises(PracticeError, match="IDEMPOTENCY_CONFLICT"):
        await service.complete_session(owner_id, session.id, changed)
    with pytest.raises(PracticeError, match="PRACTICE_NOT_FOUND"):
        await service.complete_session(outsider_id, session.id, correct)

    expired_owner, _ = await _seed_practice(db_session, exercise_count=1)
    expired = await service.create_session(
        expired_owner.id, at=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    )
    expired_payload = PracticeCompletion(
        answers=[PracticeAnswer(item_id=expired.items[0].id, answer="yes")]
    )
    with pytest.raises(PracticeError, match="PRACTICE_EXPIRED"):
        await service.complete_session(
            expired_owner.id,
            expired.id,
            expired_payload,
            at=datetime(2026, 1, 1, 12, 16, tzinfo=timezone.utc),
        )


async def test_exercise_deletion_preserves_practice_snapshot(db_session):
    """Keeps immutable practice history while removing live exercise references."""
    from backend.models.exercise_submission import ExerciseSubmission
    from backend.models.practice import PracticeSessionItem
    from backend.models.review_item import ReviewItem
    from backend.repositories.exercise_repo import ExerciseRepository
    from backend.repositories.gamification_repo import GamificationRepository
    from backend.repositories.practice_repo import PracticeRepository
    from backend.services.practice_service import PracticeService

    user, exercises = await _seed_practice(db_session, exercise_count=1)
    practice = PracticeService(
        PracticeRepository(db_session), GamificationRepository(db_session)
    )
    session = await practice.create_session(
        user.id, at=datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc)
    )
    db_session.add(
        ExerciseSubmission(
            user_id=user.id,
            exercise_id=exercises[0].id,
            idempotency_key="delete-snapshot",
            request_hash="a" * 64,
            response={"correct": False},
        )
    )
    await db_session.commit()

    await ExerciseRepository(db_session).delete(exercises[0])

    item = await db_session.scalar(
        select(PracticeSessionItem).where(
            PracticeSessionItem.session_id == session.id
        )
    )
    assert item is not None
    assert item.exercise_id is None
    assert item.question == "Snapshot 0"
    assert await db_session.scalar(
        select(func.count()).select_from(ReviewItem).where(
            ReviewItem.exercise_id == exercises[0].id
        )
    ) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(ExerciseSubmission).where(
            ExerciseSubmission.exercise_id == exercises[0].id
        )
    ) == 0
