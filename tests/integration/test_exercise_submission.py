import importlib
from importlib import util
import asyncio
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.models.achievement import UserAchievement
from backend.models.course import Course, LevelChoices
from backend.models.exercise import Exercise, ExerciseType
from backend.models.exercise_progress import UserExerciseProgress
from backend.models.exercise_submission import ExerciseSubmission
from backend.models.gamification import Hearts, XPHistory
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.models.progress import UserProgress
from backend.models.user import UserRole
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.schemas.exercise_schema import ExerciseSubmit
from backend.services.auth_ser import AuthService
from backend.services.exercise_service import ExerciseService


pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


class FailingAchievementRepository(AchievementRepository):
    async def get_all(self):
        raise RuntimeError("late achievement failure")


def submission_repository(session):
    assert util.find_spec("backend.repositories.exercise_submission_repo") is not None
    module = importlib.import_module("backend.repositories.exercise_submission_repo")
    return module.ExerciseSubmissionRepository(session)


def exercise_service(session,achievement_repository=None):
    return ExerciseService(
        ExerciseRepository(session),
        ProgressRepository(session),
        ExerciseProgressRepository(session),
        GamificationRepository(session),
        achievement_repository or AchievementRepository(session),
        submission_repository(session),
    )


async def seed_exercise(session, *, correct_answer="hello", role=UserRole.USER):
    user = await AuthService(session).register(
        f"exercise-{uuid.uuid4().hex}@example.com",
        f"exercise_{uuid.uuid4().hex}",
        "password123",
    )
    user.role = role
    language = Language(
        code=f"e-{uuid.uuid4().hex[:6]}",
        name=f"Exercise {uuid.uuid4().hex}",
        is_active=True,
    )
    session.add(language)
    await session.flush()
    course = Course(
        language_id=language.id,
        title="A1",
        description="A1",
        level=LevelChoices.A1,
        order=1,
    )
    session.add(course)
    await session.flush()
    lesson = Lesson(course_id=course.id,title="First",order=1)
    session.add(lesson)
    await session.flush()
    exercise = Exercise(
        lesson_id=lesson.id,
        type=ExerciseType.CHOICE,
        question="Say hello",
        options={"items":["hello","bye"]},
        correct_answer=correct_answer,
    )
    session.add(exercise)
    await session.commit()
    return user,exercise


async def test_wrong_answer_replay_loses_one_heart_only(db_session):
    user,exercise = await seed_exercise(db_session)
    service = exercise_service(db_session)

    first = await service.submit_exercise(
        exercise.id,ExerciseSubmit(answer="bye"),user.id,"wrong-once"
    )
    replay = await service.submit_exercise(
        exercise.id,ExerciseSubmit(answer="bye"),user.id,"wrong-once"
    )
    hearts = await db_session.scalar(select(Hearts).where(Hearts.user_id == user.id))

    assert first == replay
    assert hearts.hearts == 4


async def test_concurrent_replay_loses_one_heart_only(db_session,test_database_url):
    user,exercise = await seed_exercise(db_session)
    user_id = user.id
    exercise_id = exercise.id
    engine = create_async_engine(test_database_url)
    session_factory = async_sessionmaker(engine,expire_on_commit=False)

    async def submit_once():
        async with session_factory() as session:
            return await exercise_service(session).submit_exercise(
                exercise_id,
                ExerciseSubmit(answer="bye"),
                user_id,
                "concurrent-wrong-once",
            )

    try:
        first,replay = await asyncio.gather(submit_once(),submit_once())
    finally:
        await engine.dispose()

    db_session.expire_all()
    hearts = await db_session.scalar(select(Hearts).where(Hearts.user_id == user_id))
    submission_count = await db_session.scalar(
        select(func.count()).select_from(ExerciseSubmission).where(
            ExerciseSubmission.user_id == user_id
        )
    )
    progress_count = await db_session.scalar(
        select(func.count()).select_from(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user_id,
            UserExerciseProgress.exercise_id == exercise_id,
        )
    )
    xp_count = await db_session.scalar(
        select(func.count()).select_from(XPHistory).where(XPHistory.user_id == user_id)
    )

    assert first == replay
    assert hearts.hearts == 4
    assert submission_count == 1
    assert progress_count == 1
    assert xp_count == 0


async def test_reusing_key_with_another_answer_is_a_conflict(db_session):
    user,exercise = await seed_exercise(db_session)
    service = exercise_service(db_session)
    await service.submit_exercise(
        exercise.id,ExerciseSubmit(answer="bye"),user.id,"changed-payload"
    )

    with pytest.raises(ValueError,match="IDEMPOTENCY_CONFLICT"):
        await service.submit_exercise(
            exercise.id,ExerciseSubmit(answer="hello"),user.id,"changed-payload"
        )


async def test_submission_joins_transaction_started_by_api_reads(db_session):
    user,exercise = await seed_exercise(db_session)
    await db_session.execute(select(Exercise).where(Exercise.id == exercise.id))

    result = await exercise_service(db_session).submit_exercise(
        exercise.id,
        ExerciseSubmit(answer="hello"),
        user.id,
        "after-api-read",
    )

    assert result.correct is True


async def test_first_correct_completion_awards_xp_once(db_session):
    user,exercise = await seed_exercise(db_session)
    service = exercise_service(db_session)

    await service.submit_exercise(
        exercise.id,ExerciseSubmit(answer="hello"),user.id,"correct-first"
    )
    await service.submit_exercise(
        exercise.id,ExerciseSubmit(answer="hello"),user.id,"correct-practice"
    )
    xp = await db_session.scalar(
        select(func.coalesce(func.sum(XPHistory.xp),0)).where(XPHistory.user_id == user.id)
    )
    progress_count = await db_session.scalar(
        select(func.count()).select_from(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user.id,
            UserExerciseProgress.exercise_id == exercise.id,
        )
    )

    assert xp == 10
    assert progress_count == 1


async def test_late_failure_rolls_back_all_game_state(db_session):
    user,exercise = await seed_exercise(db_session)
    user_id = user.id
    service = exercise_service(db_session,FailingAchievementRepository(db_session))

    with pytest.raises(RuntimeError,match="late achievement failure"):
        await service.submit_exercise(
            exercise.id,ExerciseSubmit(answer="hello"),user.id,"must-rollback"
        )

    assert await db_session.scalar(
        select(func.count()).select_from(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user_id
        )
    ) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(UserProgress).where(UserProgress.user_id == user_id)
    ) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(XPHistory).where(XPHistory.user_id == user_id)
    ) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(UserAchievement).where(
            UserAchievement.user_id == user_id
        )
    ) == 0


async def test_admin_preview_has_no_game_state_side_effects(db_session):
    user,exercise = await seed_exercise(db_session,role=UserRole.ADMIN)
    await db_session.execute(
        Hearts.__table__.delete().where(Hearts.user_id == user.id)
    )
    await db_session.commit()
    service = exercise_service(db_session)

    result = await service.submit_exercise(
        exercise.id,
        ExerciseSubmit(answer="hello"),
        user.id,
        "admin-preview",
        is_admin=True,
    )

    assert result.correct is True
    assert await db_session.scalar(
        select(func.count()).select_from(Hearts).where(Hearts.user_id == user.id)
    ) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user.id
        )
    ) == 0
