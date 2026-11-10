import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.models.course import Course, LevelChoices
from backend.models.exercise import Exercise, ExerciseType
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.models.review_item import ReviewItem
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.exercise_submission_repo import ExerciseSubmissionRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.repositories.review_repo import ReviewRepository
from backend.schemas.exercise_schema import ExerciseSubmit
from backend.services.auth_ser import AuthService
from backend.services.exercise_service import ExerciseService
from backend.services.review_service import ReviewService

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def _seed_exercises(session, count=2):
    user = await AuthService(session).register(
        f"review-{uuid.uuid4().hex}@example.com",
        f"review_{uuid.uuid4().hex}",
        "password123",
    )
    language = Language(
        code=f"r-{uuid.uuid4().hex[:6]}",
        name=f"Review {uuid.uuid4().hex}",
        is_active=True,
    )
    session.add(language)
    await session.flush()
    course = Course(
        language_id=language.id,
        title="Review A1",
        description="Review",
        level=LevelChoices.A1,
        order=1,
    )
    session.add(course)
    await session.flush()
    lesson = Lesson(course_id=course.id, title="Review", order=1)
    session.add(lesson)
    await session.flush()
    exercises = [
        Exercise(
            lesson_id=lesson.id,
            type=ExerciseType.CHOICE,
            question=f"Question {index}",
            options={"items": ["yes", "no"]},
            correct_answer="yes",
        )
        for index in range(count)
    ]
    session.add_all(exercises)
    await session.commit()
    return user, exercises


async def test_due_reviews_are_ordered_paged_and_user_isolated(db_session):
    """Catches due rows leaking between users or unstable page ordering."""
    first, exercises = await _seed_exercises(db_session, count=2)
    second, second_exercises = await _seed_exercises(db_session, count=1)
    service = ReviewService(ReviewRepository(db_session))
    base = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    await service.record_result(first.id, exercises[0].id, False, base, commit=True)
    await service.record_result(
        first.id, exercises[1].id, False, base - timedelta(hours=1), commit=True
    )
    await service.record_result(
        second.id, second_exercises[0].id, False, base - timedelta(hours=2), commit=True
    )

    page = await service.get_due(first.id, limit=1, offset=0, at=base)
    second_page = await service.get_due(first.id, limit=1, offset=1, at=base)

    assert page.total == 2
    assert [item.exercise_id for item in page.items] == [exercises[1].id]
    assert [item.exercise_id for item in second_page.items] == [exercises[0].id]


async def test_exercise_submission_records_review_once_on_replay(db_session):
    """Catches idempotent exercise replay advancing review twice."""
    user, exercises = await _seed_exercises(db_session, count=1)
    review_service = ReviewService(ReviewRepository(db_session))
    service = ExerciseService(
        ExerciseRepository(db_session),
        ProgressRepository(db_session),
        ExerciseProgressRepository(db_session),
        GamificationRepository(db_session),
        AchievementRepository(db_session),
        ExerciseSubmissionRepository(db_session),
        review_service,
    )

    await service.submit_exercise(
        exercises[0].id,
        ExerciseSubmit(answer="yes"),
        user.id,
        "review-once",
    )
    await service.submit_exercise(
        exercises[0].id,
        ExerciseSubmit(answer="yes"),
        user.id,
        "review-once",
    )
    item = await db_session.scalar(
        select(ReviewItem).where(
            ReviewItem.user_id == user.id,
            ReviewItem.exercise_id == exercises[0].id,
        )
    )

    assert item.attempts == 1
    assert item.box == 1
