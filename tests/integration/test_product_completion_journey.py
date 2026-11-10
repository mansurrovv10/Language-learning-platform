import uuid
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from backend.models.course import Course, LevelChoices
from backend.models.exercise import Exercise, ExerciseType
from backend.models.gamification import Hearts, XPHistory
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.daily_goal_repo import DailyGoalRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.exercise_submission_repo import ExerciseSubmissionRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.practice_repo import PracticeRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.repositories.review_repo import ReviewRepository
from backend.schemas.exercise_schema import ExerciseSubmit
from backend.schemas.practice_schema import PracticeAnswer, PracticeCompletion
from backend.services.auth_ser import AuthService
from backend.services.daily_goal_service import DailyGoalService
from backend.services.exercise_service import ExerciseService
from backend.services.practice_service import PracticeService
from backend.services.review_service import ReviewService
from backend.time import utc_now

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def _seed_journey(session):
    user = await AuthService(session).register(
        f"journey-{uuid.uuid4().hex}@example.com",
        f"journey_{uuid.uuid4().hex}",
        "password123",
    )
    language = Language(
        code=f"j-{uuid.uuid4().hex[:6]}",
        name=f"Journey {uuid.uuid4().hex}",
        is_active=True,
    )
    session.add(language)
    await session.flush()
    course = Course(
        language_id=language.id,
        title="Journey A1",
        description="Release journey",
        level=LevelChoices.A1,
        order=1,
    )
    session.add(course)
    await session.flush()
    lesson = Lesson(course_id=course.id, title="Journey", order=1)
    session.add(lesson)
    await session.flush()
    exercises = [
        Exercise(
            lesson_id=lesson.id,
            type=ExerciseType.CHOICE,
            question=f"Choose yes {position}",
            options={"items": ["yes", "no"]},
            correct_answer="yes",
        )
        for position in range(3)
    ]
    session.add_all(exercises)
    await session.commit()
    return user, exercises


def _exercise_service(session, review_service):
    return ExerciseService(
        ExerciseRepository(session),
        ProgressRepository(session),
        ExerciseProgressRepository(session),
        GamificationRepository(session),
        AchievementRepository(session),
        ExerciseSubmissionRepository(session),
        review_service,
    )


async def test_complete_learning_recovery_journey(db_session):
    """Verifies the release path across hearts, review, practice, XP and goals."""
    user, exercises = await _seed_journey(db_session)
    review = ReviewService(ReviewRepository(db_session))
    exercise = _exercise_service(db_session, review)
    instant = utc_now() + timedelta(seconds=1)

    wrong = await exercise.submit_exercise(
        exercises[0].id,
        ExerciseSubmit(answer="no"),
        user.id,
        "journey-wrong",
    )
    for candidate in exercises[1:]:
        await review.record_result(
            user.id, candidate.id, False, instant, commit=True
        )

    due = await review.get_due(user.id, at=instant)
    practice = PracticeService(
        PracticeRepository(db_session), GamificationRepository(db_session)
    )
    practice_session = await practice.create_session(user.id, at=instant)
    completion = PracticeCompletion(
        answers=[
            PracticeAnswer(item_id=item.id, answer="yes")
            for item in practice_session.items
        ]
    )
    practiced = await practice.complete_session(
        user.id, practice_session.id, completion, at=instant
    )
    replay = await practice.complete_session(
        user.id, practice_session.id, completion, at=instant
    )

    correct = await exercise.submit_exercise(
        exercises[1].id,
        ExerciseSubmit(answer="yes"),
        user.id,
        "journey-correct",
    )
    goal = await DailyGoalService(DailyGoalRepository(db_session)).get_status(
        user.id
    )
    hearts = await db_session.scalar(
        select(Hearts).where(Hearts.user_id == user.id)
    )
    xp = await db_session.scalar(
        select(func.coalesce(func.sum(XPHistory.xp), 0)).where(
            XPHistory.user_id == user.id
        )
    )

    assert wrong.correct is False
    assert wrong.hearts_left == 4
    assert due.total == 3
    assert practiced.heart_awarded is True
    assert practiced.hearts_left == 5
    assert replay == practiced
    assert correct.correct is True
    assert hearts.hearts == 5
    assert xp == 10
    assert goal.earned_xp == 10
